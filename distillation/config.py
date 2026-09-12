"""
Sovereign Gotham - Distillation Configuration
Defines paths, models, hardware settings, and curation thresholds for Teacher-Student distillation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class DistillationConfig(BaseModel):
    """Centralized configuration for distillation environment."""
    
    # Storage Paths (Prioritize Drive D:)
    storage_root: Path = Field(
        default=Path("D:/sovereign_distillation") if Path("D:/").exists() else Path("./distillation_data")
    )
    harvested_data_dir: Path = Field(
        default=Path("D:/sovereign_gotham_data") if Path("D:/").exists() else Path("./sample_data")
    )
    
    # Models
    student_model_id: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    teacher_model_name: str = "deepseek-r1-large"
    
    # Hardware & Backend
    device_index: int = 1  # AMD Radeon RX 7600 XT
    gpu_name: str = "AMD Radeon RX 7600 XT (16 GB GDDR6)"
    use_directml: bool = True
    
    # Hyperparameters for Student Distillation
    max_seq_length: int = 512
    batch_size: int = 1
    grad_accum: int = 4
    learning_rate: float = 2e-4
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    
    # Quality & Curation Gates (DSpark Curator)
    min_thought_steps: int = 3
    min_reasoning_length: int = 120
    require_valid_json_output: bool = True
    enforce_roe_compliance: bool = True
    
    @property
    def teacher_raw_dir(self) -> Path:
        p = self.storage_root / "teacher_raw"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def curated_dataset_path(self) -> Path:
        p = self.storage_root / "curated_dataset"
        p.mkdir(parents=True, exist_ok=True)
        return p / "distilled_sovereign_r1.jsonl"

    @property
    def student_output_dir(self) -> Path:
        p = self.storage_root / "student_checkpoints"
        p.mkdir(parents=True, exist_ok=True)
        return p / "distilled_student_adapter"


default_distill_config = DistillationConfig()
