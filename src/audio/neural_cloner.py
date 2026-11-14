"""Neural Tone Color Converter for zero-shot voice cloning.

Disentangles phonetic content from speaker tone color using conditional normalizing flows
and HiFi-GAN neural decoding to achieve broadcast-quality vocal identity transfer
at zero monetary cost on local GPU/CPU hardware.
"""

from __future__ import annotations

import logging
import math
import subprocess
from pathlib import Path
from typing import Optional, Union

import numpy as np
import scipy.signal
import soundfile as sf
import torch

from src.audio.openvoice import utils
from src.audio.openvoice.mel_processing import spectrogram_torch
from src.audio.openvoice.models import SynthesizerTrn
from src.audio.voicestudio import get_vocal_studio_filter

logger = logging.getLogger("visual_studio.neural_cloner")

_GLOBAL_CONVERTER: Optional["NeuralToneColorConverter"] = None


def load_audio_resampled(wav_path: Path, target_sr: int) -> np.ndarray:
    """Reads audio file and resamples to target sample rate with mono downmixing."""
    wav, sr = sf.read(str(wav_path))
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    wav = wav.astype(np.float32)

    if sr != target_sr:
        gcd = math.gcd(int(sr), int(target_sr))
        up = int(target_sr // gcd)
        down = int(sr // gcd)
        wav = scipy.signal.resample_poly(wav, up, down).astype(np.float32)

    return wav


class NeuralToneColorConverter:
    """Neural Voice Cloning engine powered by normalizing flows and HiFi-GAN vocoding."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        checkpoint_path: Optional[Path] = None,
        device: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_path = config_path or (
            base_dir / "assets" / "models" / "openvoice" / "converter" / "config.json"
        )
        self.checkpoint_path = checkpoint_path or (
            base_dir / "assets" / "models" / "openvoice" / "converter" / "checkpoint.pth"
        )

        if device is None:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading OpenVoice V2 converter config from HuggingFace...")
            import urllib.request
            urllib.request.urlretrieve(
                "https://huggingface.co/myshell-ai/OpenVoiceV2/resolve/main/converter/config.json",
                str(self.config_path),
            )

        if not self.checkpoint_path.exists():
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading OpenVoice V2 converter weights (125 MB) from HuggingFace...")
            import urllib.request
            urllib.request.urlretrieve(
                "https://huggingface.co/myshell-ai/OpenVoiceV2/resolve/main/converter/checkpoint.pth",
                str(self.checkpoint_path),
            )

        self.hps = utils.get_hparams_from_file(str(self.config_path))
        self.sampling_rate = self.hps.data.sampling_rate

        logger.info(f"Initializing NeuralToneColorConverter on device: {self.device}")
        self.model = SynthesizerTrn(
            len(getattr(self.hps, "symbols", [])),
            self.hps.data.filter_length // 2 + 1,
            n_speakers=self.hps.data.n_speakers,
            **self.hps.model,
        ).to(self.device)

        checkpoint_dict = torch.load(str(self.checkpoint_path), map_location=torch.device(self.device))
        self.model.load_state_dict(checkpoint_dict["model"], strict=False)
        self.model.eval()
        logger.info(f"Loaded neural voice converter weights ({self.checkpoint_path.stat().st_size / 1024 / 1024:.1f} MB)")

    def extract_speaker_embedding(
        self,
        audio_path: Path,
        cache_path: Optional[Path] = None,
    ) -> torch.Tensor:
        """Extracts a continuous 256-dimensional speaker latent embedding vector."""
        if cache_path and cache_path.exists():
            try:
                emb = torch.load(str(cache_path), map_location=torch.device(self.device))
                if isinstance(emb, torch.Tensor) and emb.ndim == 3:
                    return emb.to(self.device)
            except Exception as e:
                logger.warning(f"Could not read cached embedding from {cache_path}: {e}")

        audio = load_audio_resampled(audio_path, self.sampling_rate)
        y = torch.FloatTensor(audio).to(self.device).unsqueeze(0)

        spec = spectrogram_torch(
            y,
            self.hps.data.filter_length,
            self.hps.data.sampling_rate,
            self.hps.data.hop_length,
            self.hps.data.win_length,
            center=False,
        ).to(self.device)

        with torch.no_grad():
            speaker_embedding = self.model.ref_enc(spec.transpose(1, 2)).unsqueeze(-1)

        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(speaker_embedding.cpu(), str(cache_path))
            logger.info(f"Saved neural speaker embedding to: {cache_path}")

        return speaker_embedding

    def convert_voice(
        self,
        source_wav: Path,
        target_se: Union[torch.Tensor, Path],
        output_wav: Path,
        tau: float = 0.32,
    ) -> Path:
        """Transforms source speech tone color to match target speaker embedding.

        1. Extracts source speaker tone color from source audio
        2. Disentangles phonetic content via posterior normalizing flow
        3. Infuses target speaker latent conditioning vector
        4. Synthesizes high-fidelity audio via HiFi-GAN neural decoder
        5. Masters to broadcast 48 kHz stereo with vocal studio mastering
        """
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        temp_converted = output_wav.with_suffix(".neural_raw.wav")

        # Resolve target embedding
        if isinstance(target_se, Path):
            if target_se.suffix == ".pt" or target_se.suffix == ".pth":
                tgt_tensor = torch.load(str(target_se), map_location=torch.device(self.device))
            else:
                tgt_tensor = self.extract_speaker_embedding(target_se)
        else:
            tgt_tensor = target_se.to(self.device)

        # Load and compute source audio spectrogram
        src_audio = load_audio_resampled(source_wav, self.sampling_rate)
        y_src = torch.FloatTensor(src_audio).to(self.device).unsqueeze(0)

        spec_src = spectrogram_torch(
            y_src,
            self.hps.data.filter_length,
            self.hps.data.sampling_rate,
            self.hps.data.hop_length,
            self.hps.data.win_length,
            center=False,
        ).to(self.device)

        with torch.no_grad():
            # Source speaker embedding extracted directly from the base audio
            src_se = self.model.ref_enc(spec_src.transpose(1, 2)).unsqueeze(-1)
            spec_lengths = torch.LongTensor([spec_src.size(-1)]).to(self.device)

            converted_tensor, _, _ = self.model.voice_conversion(
                spec_src,
                spec_lengths,
                sid_src=src_se,
                sid_tgt=tgt_tensor,
                tau=tau,
            )

        converted_np = converted_tensor[0, 0].data.cpu().float().numpy()

        # Normalize peak amplitude to prevent clipping before mastering
        max_val = np.max(np.abs(converted_np))
        if max_val > 1e-4:
            converted_np = (converted_np / max_val) * 0.92

        sf.write(str(temp_converted), converted_np, self.sampling_rate, subtype="PCM_16")

        # Transcode & master to broadcast standard PCM 16-bit 48kHz Stereo WAV (-16 LUFS)
        cmd_master = [
            "ffmpeg",
            "-y",
            "-i", str(temp_converted),
            "-af", get_vocal_studio_filter(),
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(output_wav),
        ]
        try:
            subprocess.run(cmd_master, capture_output=True, check=True)
        finally:
            if temp_converted.exists():
                temp_converted.unlink()

        return output_wav


def get_neural_converter() -> NeuralToneColorConverter:
    """Returns singleton instance of NeuralToneColorConverter cached in memory."""
    global _GLOBAL_CONVERTER
    if _GLOBAL_CONVERTER is None:
        _GLOBAL_CONVERTER = NeuralToneColorConverter()
    return _GLOBAL_CONVERTER
