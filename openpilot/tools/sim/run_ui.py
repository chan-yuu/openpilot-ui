"""Startup script for openpilot-ui with mock data support."""

import argparse
import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from multiprocessing import Process

# Add project root to path (parent of openpilot package)
BASEDIR = Path(__file__).parent.parent.parent.parent.resolve()
if str(BASEDIR) not in sys.path:
    sys.path.insert(0, str(BASEDIR))


def run_data_simulator(mode: str, rate: int = 20, engaged: bool = False):
    """Run the data simulator in a subprocess."""
    from openpilot.selfdrive.mock.data_simulator import DataSimulator

    simulator = DataSimulator(mode=mode)
    simulator._update_rate = rate
    simulator.set_engaged(engaged)

    print("Data simulator started")
    simulator.run()


def run_ui(width: int, height: int, fullscreen: bool = False):
    """Run the UI application."""
    # Set environment variables for UI
    os.environ["SCALE"] = os.environ.get("SCALE", "1.0")

    # Import and run UI
    from openpilot.selfdrive.ui.ui import main as ui_main

    # Override sys.argv for UI
    ui_args = ["ui"]
    if fullscreen:
        # raylib fullscreen is handled in application
        pass
    sys.argv = ui_args

    ui_main()


def main():
    parser = argparse.ArgumentParser(
        description="Openpilot UI standalone launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  demo     - Use simulated data (default)
  camera   - Use real camera input
  vehicle  - Connect to real vehicle (requires hardware)

Examples:
  %(prog)s --mode demo
  %(prog)s --mode camera --device 0
  %(prog)s --width 1920 --height 1080 --fullscreen

Keyboard shortcuts (in demo mode):
  Space    - Toggle engagement
  E        - Toggle experimental mode
  M        - Toggle metric/imperial units
  Esc      - Exit
        """
    )

    parser.add_argument("--mode", choices=["demo", "camera", "vehicle"],
                        default="demo", help="Simulation mode")
    parser.add_argument("--device", type=int, default=0,
                        help="Camera device index (for camera mode)")
    parser.add_argument("--width", type=int, default=2160,
                        help="Display width")
    parser.add_argument("--height", type=int, default=1080,
                        help="Display height")
    parser.add_argument("--fullscreen", action="store_true",
                        help="Run in fullscreen mode")
    parser.add_argument("--rate", type=int, default=20,
                        help="Data simulation rate (Hz)")
    parser.add_argument("--engaged", action="store_true",
                        help="Start in engaged state")
    parser.add_argument("--ui-only", action="store_true",
                        help="Run UI only (don't start data simulator)")

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║          openpilot-ui v0.1.0         ║
╠══════════════════════════════════════╣
║  Mode: {args.mode:<28} ║
║  Resolution: {args.width}x{args.height:<19} ║
║  Fullscreen: {str(args.fullscreen):<24} ║
╚══════════════════════════════════════╝
    """)

    processes = []

    def signal_handler(sig, frame):
        print("\nStopping...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start data simulator if needed
    # We only start one simulator - in the main process thread for keyboard control
    # NOT in a separate process to avoid MultiplePublishersError

    # Start UI
    print("Starting UI...")
    try:
        # For now, we run UI in the main process
        from openpilot.selfdrive.ui.layouts.main import MainLayout
        from openpilot.system.ui.lib.application import gui_app

        # Initialize and run
        gui_app.init_window("openpilot-ui", fps=args.rate)

        # Create main layout
        main_layout = MainLayout()

        print("\nControls:")
        print("  Space - Toggle engagement")
        print("  E     - Toggle experimental mode")
        print("  M     - Toggle metric/imperial")
        print("  Esc   - Exit")
        print()

        # Update state reference for keyboard control
        from openpilot.selfdrive.ui.ui_state import ui_state
        from openpilot.selfdrive.mock.data_simulator import DataSimulator

        # Create a local simulator for data and keyboard control
        if args.mode == "demo":
            local_sim = DataSimulator(mode="demo")
            local_sim.set_engaged(args.engaged)
            local_sim.run_in_thread()

            # Keyboard handler
            import pyray as rl
            for _ in gui_app.render():
                ui_state.update()
                local_sim._engaged = local_sim.mock_selfdrive._enabled  # Sync state

                # Handle keyboard
                if rl.is_key_released(rl.KeyboardKey.KEY_SPACE):
                    local_sim.toggle_engaged()

                if rl.is_key_released(rl.KeyboardKey.KEY_E):
                    local_sim.toggle_experimental()

                if rl.is_key_released(rl.KeyboardKey.KEY_M):
                    from openpilot.common.params import Params
                    params = Params()
                    params.put_bool("IsMetric", not params.get_bool("IsMetric"))
        else:
            # Just run UI without keyboard control
            for _ in gui_app.render():
                ui_state.update()

    except ImportError as e:
        print(f"Error importing UI components: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"Error running UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    main()