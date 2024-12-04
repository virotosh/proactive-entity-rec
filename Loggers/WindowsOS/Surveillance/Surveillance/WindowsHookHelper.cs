using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;

namespace Surveillance
{
    class WindowsHookHelper
    {
        public delegate IntPtr HookDelegate(
            Int32 Code, IntPtr wParam, IntPtr lParam);

        [DllImport("User32.dll")]
        public static extern IntPtr CallNextHookEx(
            IntPtr hHook, Int32 nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("User32.dll")]
        public static extern IntPtr UnhookWindowsHookEx(IntPtr hHook);


        [DllImport("User32.dll")]
        public static extern IntPtr SetWindowsHookEx(
            Int32 idHook, HookDelegate lpfn, IntPtr hmod,
            Int32 dwThreadId);
    }
}
