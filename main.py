from game import run
import traceback
import sys

if __name__ == "__main__":
    try:
        run()
    except Exception:
        # Log to file
        with open("crash_log_global.txt", "w") as f:
            traceback.print_exc(file=f)
        
        # Print to console
        traceback.print_exc()
        print("\nCRASH DETECTED! Log written to crash_log_global.txt")
        input("Press Enter to exit...")