"""Launch the course simulation in the dedicated modern Python/Tk environment.

Direct execution also selects Module_6/.venv, even from the root environment.
Only startup and the symbol-image renderer are adapted; the solver is unchanged.
"""
from __future__ import annotations

import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile

# Support users running this file directly with their editor's selected Python.
if __name__ == "__main__":
    gui_python = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"
    # Compare the environment directory, not resolved executable symlinks.
    if Path(sys.prefix).absolute() != gui_python.parent.parent.absolute():
        if not gui_python.is_file():
            raise SystemExit("Module 6 GUI environment missing: " + str(gui_python))
        os.execv(str(gui_python), [str(gui_python), str(Path(__file__).resolve()), *sys.argv[1:]])

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "phys39_matplotlib_cache"))


def load_simulation():
    source = Path(__file__).resolve().with_name("Lab_6_7_modeling_tec_v3.py")
    spec = importlib.util.spec_from_file_location("phys39_course_simulation", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    def render_math_symbol(self, expression):
        # Pillow transfers pixels to Tk without relying on Tk's PNG decoder.
        from PIL import Image, ImageTk

        buffer = io.BytesIO()
        with self.matplotlib.rc_context({"savefig.transparent": True}):
            self.math_to_image(
                f"${expression}$", buffer,
                prop=self.FontProperties(size=13.5), dpi=120,
                format="png", color="black",
            )
        buffer.seek(0)
        with Image.open(buffer) as png:
            image = ImageTk.PhotoImage(png.convert("RGBA"), master=self.root)
        self.math_symbol_images.append(image)
        return image

    module.ModelingTECv3Gui._render_math_symbol = render_math_symbol
    return module


def startup_check(module):
    """Check image rendering, controller/model switches and drawing, then exit."""
    root = module.tk.Tk()
    try:
        gui = module.ModelingTECv3Gui(root)
        root.update_idletasks()
        for process in ("one_lump", "two_lump"):
            gui.process_mode.set(process)
            gui._change_process(None)
            for controller in ("open_loop", "p", "pi"):
                gui.controller_mode.set(controller)
                gui._change_controller(None)
                gui._draw()
                root.update_idletasks()
                print(f"PASS: {process}/{controller}")
        print(f"GUI startup passed; Tk {root.tk.call('info', 'patchlevel')}; "
              f"{len(gui.math_symbol_images)} symbol images rendered.")
    finally:
        root.destroy()


if __name__ == "__main__":
    try:
        simulation = load_simulation()
        if sys.argv[1:] == ["--check"]:
            startup_check(simulation)
        else:
            simulation.main()
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Missing dependency: {exc.name}. Install Module_6/python/requirements-gui.txt "
            "in Module_6/.venv."
        ) from exc
