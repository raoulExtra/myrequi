# GPU info

Observed on this Android device:

- `ro.hardware.egl = adreno`
- `ro.hardware.vulkan = adreno`
- `/dev/kgsl-3d0` exists
- `/dev/dri/renderD128` exists

Conclusion: the device appears to have an **Adreno GPU** and GPU-capable device nodes are present.

Notes:
- no display session variables were set (`DISPLAY`, `WAYLAND_DISPLAY`)
- this does not by itself prove a specific compute stack is usable, only that GPU hardware is present
