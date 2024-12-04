using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Surveillance
{
    public class MouseInput : IDisposable
    {
        public event EventHandler<EventArgs> MouseWheel;
        public event EventHandler<EventArgs> MouseRClick;
        public event EventHandler<EventArgs> MouseLClick;

        private WindowsHookHelper.HookDelegate mouseDelegate;
        private IntPtr mouseHandle;
        private const Int32 WH_MOUSE_LL = 14;
        private const int WM_LBUTTONDOWN = 0x0201;
        private const int WM_RBUTTONDOWN = 0x0204;
        private const int WM_MOUSEHWHEEL = 0x020A;

        private bool disposed;

        public MouseInput()
        {
            mouseDelegate = MouseHookDelegate;
            mouseHandle = WindowsHookHelper.SetWindowsHookEx(WH_MOUSE_LL, mouseDelegate, IntPtr.Zero, 0);
        }

        private IntPtr MouseHookDelegate(Int32 Code, IntPtr wParam, IntPtr lParam)
        {
            if (Code < 0)
                return WindowsHookHelper.CallNextHookEx(mouseHandle, Code, wParam, lParam);
            if (wParam == (IntPtr)WM_MOUSEHWHEEL)
            {
                if (MouseWheel != null)
                    MouseWheel(this, new EventArgs());
            }
            if (wParam == (IntPtr)WM_RBUTTONDOWN)
            {
                if (MouseRClick != null)
                    MouseRClick(this, new EventArgs());
            }
            if (wParam == (IntPtr)WM_LBUTTONDOWN)
            {
                if (MouseLClick != null)
                    MouseLClick(this, new EventArgs());
            }

            return WindowsHookHelper.CallNextHookEx(mouseHandle, Code, wParam, lParam);
        }

        public void Dispose()
        {
            Dispose(true);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!disposed)
            {
                if (mouseHandle != IntPtr.Zero)
                    WindowsHookHelper.UnhookWindowsHookEx(mouseHandle);

                disposed = true;
            }
        }

        ~MouseInput()
        {
            Dispose(false);
        }
    }
}
