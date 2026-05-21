# JazzKeys

把全局键盘输入变成钢琴、雨滴、打字机或爵士即兴音效的小型 macOS/Python 项目。默认模式是 `jazz`，会根据打字速度生成单音、和弦和停顿伴奏。

## 运行

```bash
python3 -m pip install -r requirements.txt
python3 main.py --mode jazz
```

常用参数：

```bash
python3 main.py --list
python3 main.py --mode piano --song 1
python3 main.py --mode rain --song 4
python3 main.py --mode piano --midi /path/to/file.mid
python3 main.py --mode jazz --pomodoro 25
```

macOS 首次使用需要给运行它的终端或打包后的 App 开启辅助功能权限：系统设置 → 隐私与安全性 → 辅助功能。

## 文件结构

- `main.py`：应用入口、模式选择、爵士生成和番茄钟逻辑。
- `keyboard_listener.py`：全局键盘监听和按键分类。
- `sound_engine.py`：内置合成器、可选 FluidSynth 音源、音频输出。
- `songs.py`：内置曲目和简谱解析。
- `midi_loader.py`：MIDI 文件导入。
- `setup.py`：py2app 打包配置。
- `build_app.sh`：本机打包辅助脚本。

## 构建

```bash
python3 setup.py py2app
# 或使用本机辅助脚本
./build_app.sh
```

高级钢琴音色依赖根目录的 `Piano.sf3`。如果本机没有 FluidSynth 或音源加载失败，程序会自动回退到内置合成器。

## 当前优化方向

- 打包链路需要收敛：现在同时存在 py2app、PyInstaller spec 和 AppleScript 包装思路，建议最终只保留一条主要发布路径。
- `build_app.sh` 和部分打包配置含有本机绝对路径，后续应改成自动探测，方便换机器构建。
- 项目根目录可以继续拆分为 `src/`、`assets/`、`scripts/`，但当前代码量很小，先保持平铺更便于迭代。
- 如果要长期使用，可以增加一个最小测试集，覆盖曲谱解析、MIDI 导入和键盘分类。
