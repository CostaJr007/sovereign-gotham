@echo off
title Sovereign Gotham - Autonomous Distillation, Training & Shutdown
echo =========================================================================
echo    SOVEREIGN GOTHAM // AUTONOMOUS WORKFLOW & AUTO-SHUTDOWN
echo =========================================================================
echo Target: 250 Curated Samples
echo GPU: AMD Radeon RX 7600 XT (DirectML)
echo Model: DeepSeek-R1-Distill-Qwen-1.5B
echo.
echo Once the target is reached, training will execute, followed by
echo cognitive evaluation and a safe 2-minute shutdown countdown.
echo.
echo To abort the shutdown after it triggers, run: shutdown /a
echo =========================================================================
echo.

python scripts/run_distill_train_and_shutdown.py --target 250 --epochs 4 --shutdown_delay 120

pause
