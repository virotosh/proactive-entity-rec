using System;

namespace Surveillance
{
    public class KeyboardInput : IDisposable
    {
        public event EventHandler<EventArgs> KeyBoardKeyPressed;

        private WindowsHookHelper.HookDelegate keyBoardDelegate;
        private IntPtr keyBoardHandle;
        private const Int32 WH_KEYBOARD_LL = 13;
        private bool disposed;
        private const int WM_KEYDOWN = 0x0100;

        public KeyboardInput()
        {
            keyBoardDelegate = KeyboardHookDelegate;
            keyBoardHandle = WindowsHookHelper.SetWindowsHookEx(
                WH_KEYBOARD_LL, keyBoardDelegate, IntPtr.Zero, 0);
        }

        private IntPtr KeyboardHookDelegate(
            Int32 Code, IntPtr wParam, IntPtr lParam)
        {
            if (Code < 0)
            {
                return WindowsHookHelper.CallNextHookEx(
                    keyBoardHandle, Code, wParam, lParam);
            }
            if (Code >= 0 && wParam == (IntPtr)WM_KEYDOWN)
            {
                if (KeyBoardKeyPressed != null)
                    KeyBoardKeyPressed(this, new EventArgs());
            }

            return WindowsHookHelper.CallNextHookEx(
                keyBoardHandle, Code, wParam, lParam);
        }

        public void Dispose()
        {
            Dispose(true);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!disposed)
            {
                if (keyBoardHandle != IntPtr.Zero)
                {
                    WindowsHookHelper.UnhookWindowsHookEx(
                        keyBoardHandle);
                }

                disposed = true;
            }
        }

        ~KeyboardInput()
        {
            Dispose(false);
        }
    }
}
