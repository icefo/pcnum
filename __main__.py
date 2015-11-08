import argparse
from backend.main import launch_backend
from GUI.MainWindow import launch_gui


if __name__ == '__main__':
    # doc: http://blog.ablepear.com/2012/10/bundling-python-files-into-stand-alone.html
    # Get the arguments, if any
    parser = argparse.ArgumentParser(description="capture software, this package contains the backend and the GUI")
    parser.add_argument("-backend", "--Launch_backend", action="store_true", help="Launch the backend")
    parser.add_argument("-GUI", "--Launch_GUI", action="store_true", help="Launch the GUI")
    args = parser.parse_args()

    if args.Launch_backend:
        launch_backend()
    elif args.Launch_GUI:
        launch_gui()
    else:
        raise ValueError("type -h for help")
