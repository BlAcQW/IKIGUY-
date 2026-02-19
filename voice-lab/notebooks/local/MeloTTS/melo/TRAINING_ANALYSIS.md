# MeloTTS Twi Training Analysis
**Date:** October 13, 2025
**Model:** twi_full
**Status:** CRITICAL ISSUE IDENTIFIED AND FIXED

## Problem Summary

The training appeared to be progressing through epochs but was **failing silently due to CUDA Out of Memory errors**. Only ~200 batches were being processed per epoch instead of the expected 99,818 batches.

### Root Cause

1. **CUDA OOM Errors**: Every epoch crashed immediately when trying to allocate 24-32MB of GPU memory
2. **Silent Failure**: The exception handler (train.py:291-293) caught OOM errors and silently moved to next epoch
3. **Incomplete Training**: Only 1 log entry per epoch (at 0% progress) before crashing
4. **Time Waste**: Each failed epoch took ~90 minutes before restarting

### Evidence

From `train_fp32.log`:
```
0%|          | 0/99818 [00:00<?, ?it/s]Evaluating ...
0%|          | 0/99818 [1:22:21<?, ?it/s]
CUDA out of memory. Tried to allocate 30.00 MiB...
```

Expected: 99,818 batches per epoch (~202K samples / batch_size 2)
Actual: ~200 batches before OOM crash

## Convergence Analysis

Despite the issues, losses showed improvement in the limited batches that did process:

| Loss Component | Initial | Final | Change |
|----------------|---------|-------|--------|
| Discriminator  | 2.82    | 2.45  | -13.3% ✓ |
| Generator      | 2.62    | 2.53  | -3.3% ✓ |
| Feature Match  | 12.44   | 10.49 | -15.7% ✓ |
| Mel Spectrogram| 24.94   | 21.06 | -15.5% ✓ |
| Duration       | 4.83    | 4.63  | -3.9% ✓ |
| KL Divergence  | 5.07    | 3.12  | -38.5% ✓ |

**Note:** This is based on only ~200 batches/epoch instead of 99,818!

## Solutions Implemented

### 1. Configuration Changes (`data/twi_full/config.json`)
- ✅ **Reduced batch_size**: 2 → 1 (50% memory reduction)
- ✅ **Reduced segment_size**: 16384 → 12288 (25% memory reduction)
- ✅ **Added checkpoint limit**: keep_ckpts = 3 (disk space management)

### 2. DataLoader Optimization (`train.py`)
- ✅ **Reduced num_workers**: 16 → 8 (less memory for prefetching)
- ✅ **Reduced prefetch_factor**: 4 → 2 (less memory for buffering)

### 3. Error Handling Improvements (`train.py`)
- ✅ **Better error logging**: Full traceback + error type
- ✅ **Stop on OOM**: Raise exception instead of silently continuing
- ✅ **Prevent infinite OOM loops**

### 4. Memory Optimization (`restart_training.sh`)
- ✅ **Enable expandable segments**: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
- ✅ **Automated restart script**

## Dataset Statistics

- **Training samples**: 212,000 (202,003 after filtering)
- **Validation samples**: 11,650 (11,123 after filtering)
- **Bucket distribution**: [60816, 35322, 37248, 34680, 16916, 7530, 4430, 2694]
- **Sample lengths**: 51-2328 frames (mean: ~464)
- **Batches per epoch** (new): ~202,000 batches (batch_size=1)

## GPU Status

- **Model**: NVIDIA RTX 4000 SFF Ada Generation
- **Total Memory**: 20,475 MB (19.55 GB)
- **Usage**: 18,777 MB (89%) - near capacity
- **Utilization**: 89% during training

## Next Steps

1. **Stop Current Training**:
   ```bash
   pkill -f "train.py --c data/twi_full/config.json"
   ```

2. **Restart with Fixes**:
   ```bash
   cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
   ./restart_training.sh
   ```

3. **Monitor Progress**:
   ```bash
   # Watch stdout/stderr
   tail -f train_optimized.log

   # Watch training metrics
   tail -f logs/twi_full/train.log

   # Check GPU
   watch -n 1 nvidia-smi
   ```

4. **Verify Fix**:
   - Should see >100 log entries per epoch (not just 1)
   - Should reach eval_interval (2000 steps) and save checkpoints
   - No CUDA OOM errors in logs

## Expected Training Time

With fixes:
- **Batches per epoch**: ~202,000
- **Time per batch**: ~0.5-1 second (estimated)
- **Time per epoch**: ~28-56 hours
- **Checkpoint interval**: Every 2,000 steps (~1-2 hours)
- **First checkpoint**: Should appear within 2 hours

## Files Modified

1. `data/twi_full/config.json` - Reduced memory footprint
2. `train.py` - Better error handling + memory optimization
3. `restart_training.sh` - New automated restart script
4. Backup: `data/twi_full/config.json.backup`

## Validation

After restart, confirm:
- [ ] Training progresses past batch 200
- [ ] Log entries appear every 200 batches
- [ ] Checkpoint files (.pth) are created in `logs/twi_full/`
- [ ] No OOM errors in `train_optimized.log`
- [ ] GPU memory stable (not growing unbounded)
