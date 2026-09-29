using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace MaiHengJie
{
    class Program
    {
        static void Main(string[] args)
        {
            // ★ 关键：设置控制台UTF-8编码，否则颜文字会乱码
            Console.OutputEncoding = Encoding.UTF8;
            Console.InputEncoding = Encoding.UTF8;
            Console.Title = "脉衡界 - 校园健康智能体";

            // ── 横幅 ──
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine();
            Console.WriteLine("  +--------------------------------------+");
            Console.WriteLine("  |                                      |");
            Console.WriteLine("  |        脉衡界 · 校园健康智能体        |");
            Console.WriteLine("  |                                      |");
            Console.WriteLine("  |        一键启动器 ٩(◕‿◕)۶            |");
            Console.WriteLine("  |        你的健康，我来守护             |");
            Console.WriteLine("  |              (๑•̀ㅂ•́)و✧               |");
            Console.WriteLine("  |                                      |");
            Console.WriteLine("  +--------------------------------------+");
            Console.ResetColor();
            Console.WriteLine();

            // ── 定位项目根目录 ──
            string rootDir = AppDomain.CurrentDomain.BaseDirectory;
            if (rootDir.EndsWith("bin\\") || rootDir.EndsWith("bin/"))
                rootDir = Directory.GetParent(rootDir).FullName;

            string startPy = Path.Combine(rootDir, "start.py");

            if (!File.Exists(startPy))
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("  [!] 找不到 start.py");
                Console.WriteLine("      路径: " + startPy);
                Console.WriteLine("      请确保启动器位于项目根目录。");
                Console.ResetColor();
                Console.WriteLine("\n  按任意键退出...");
                Console.ReadKey();
                return;
            }

            Console.WriteLine("  项目路径: " + rootDir);
            Console.WriteLine();

            // ── 查找 Python ──
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.Write("  (｡･ω･｡) 正在查找 Python");
            Console.ResetColor();

            string python = FindPython();
            Console.WriteLine();

            if (python == null)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("\n  [!] 未找到 Python 环境 (；´д｀)");
                Console.WriteLine("      请安装 Python 3.8+ 并加入 PATH");
                Console.WriteLine("      下载: https://www.python.org/downloads/");
                Console.ResetColor();
                Console.WriteLine("\n  按任意键退出...");
                Console.ReadKey();
                return;
            }

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("  ✧ 已找到: " + python);
            Console.ResetColor();
            Console.WriteLine();

            // ── 启动 start.py ──
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine("  ──────────────────────────────────────");
            Console.WriteLine("  正在启动脉衡界... ε=ε=ε=(~￣▽￣)~");
            Console.WriteLine("  ──────────────────────────────────────");
            Console.ResetColor();
            Console.WriteLine();

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = python;
            psi.Arguments = "\"" + startPy + "\"";
            psi.WorkingDirectory = rootDir;
            psi.UseShellExecute = false;

            try
            {
                Process p = Process.Start(psi);
                p.WaitForExit();
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("  [!] 启动失败: " + ex.Message);
                Console.ResetColor();
                Console.WriteLine("\n  按任意键退出...");
                Console.ReadKey();
            }
        }

        /// <summary>
        /// 查找最佳 Python（优先已装 flask 的）
        /// </summary>
        static string FindPython()
        {
            // 收集候选路径
            string[] candidates = CollectPythonCandidates();

            // 逐个闪烁点表示在搜索
            foreach (string c in candidates)
            {
                Console.Write(".");
            }

            // 优先返回已装 flask 的
            foreach (string c in candidates)
            {
                if (HasFlask(c))
                    return c;
            }

            // 退而求其次
            foreach (string c in candidates)
            {
                if (VerifyPython(c))
                    return c;
            }

            return null;
        }

        static string[] CollectPythonCandidates()
        {
            System.Collections.Generic.List<string> list =
                new System.Collections.Generic.List<string>();

            // 1. where python
            AddWhereResults(list, "python");
            AddWhereResults(list, "python3");

            // 2. 常见路径
            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);

            string[] commonPaths = new string[]
            {
                Path.Combine(localApp, "Programs\\Python\\Python313\\python.exe"),
                Path.Combine(localApp, "Programs\\Python\\Python312\\python.exe"),
                Path.Combine(localApp, "Programs\\Python\\Python311\\python.exe"),
                Path.Combine(localApp, "Programs\\Python\\Python310\\python.exe"),
                Path.Combine(localApp, "Programs\\Python\\Python39\\python.exe"),
                "C:\\Python313\\python.exe",
                "C:\\Python312\\python.exe",
                "C:\\Python311\\python.exe",
                "C:\\Python310\\python.exe",
                "C:\\Python39\\python.exe",
                "C:\\Anaconda3\\python.exe",
                "C:\\Miniconda3\\python.exe",
                Path.Combine(userProfile, "anaconda3\\python.exe"),
                Path.Combine(userProfile, "miniconda3\\python.exe"),
            };

            foreach (string p in commonPaths)
            {
                if (File.Exists(p) && !list.Contains(p))
                    list.Add(p);
            }

            // 3. 过滤 Windows Store 别名
            System.Collections.Generic.List<string> filtered =
                new System.Collections.Generic.List<string>();
            foreach (string c in list)
            {
                if (!c.Contains("WindowsApps"))
                    filtered.Add(c);
            }

            return filtered.Count > 0 ? filtered.ToArray() : list.ToArray();
        }

        static void AddWhereResults(System.Collections.Generic.List<string> list, string cmd)
        {
            try
            {
                Process p = new Process();
                p.StartInfo.FileName = "where";
                p.StartInfo.Arguments = cmd;
                p.StartInfo.UseShellExecute = false;
                p.StartInfo.RedirectStandardOutput = true;
                p.StartInfo.CreateNoWindow = true;
                p.Start();
                string output = p.StandardOutput.ReadToEnd();
                p.WaitForExit(3000);
                foreach (string line in output.Split(
                    new[] { '\r', '\n' },
                    StringSplitOptions.RemoveEmptyEntries))
                {
                    string t = line.Trim();
                    if (File.Exists(t) && !list.Contains(t))
                        list.Add(t);
                }
            }
            catch { }
        }

        static bool VerifyPython(string path)
        {
            try
            {
                Process p = new Process();
                p.StartInfo.FileName = path;
                p.StartInfo.Arguments = "--version";
                p.StartInfo.UseShellExecute = false;
                p.StartInfo.RedirectStandardOutput = true;
                p.StartInfo.RedirectStandardError = true;
                p.StartInfo.CreateNoWindow = true;
                p.Start();
                string out1 = p.StandardOutput.ReadToEnd();
                string out2 = p.StandardOutput.ReadToEnd();
                p.WaitForExit(5000);
                return (out1 + out2).Contains("Python 3");
            }
            catch { return false; }
        }

        static bool HasFlask(string pythonExe)
        {
            try
            {
                string tmp = Path.Combine(Path.GetTempPath(), "_mhj_check.py");
                File.WriteAllText(tmp,
                    "try:\n" +
                    "    import flask, flask_sqlalchemy\n" +
                    "    print('OK')\n" +
                    "except:\n" +
                    "    print('NO')\n");

                Process p = new Process();
                p.StartInfo.FileName = pythonExe;
                p.StartInfo.Arguments = "\"" + tmp + "\"";
                p.StartInfo.UseShellExecute = false;
                p.StartInfo.RedirectStandardOutput = true;
                p.StartInfo.CreateNoWindow = true;
                p.Start();
                string output = p.StandardOutput.ReadToEnd();
                p.WaitForExit(8000);
                try { File.Delete(tmp); } catch { }
                return output.Contains("OK");
            }
            catch { return false; }
        }
    }
}
