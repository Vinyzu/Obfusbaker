# Obfusbaker v3.0

Obfusbaker is a Python obfuscator. It masks identifiers with Unicode glyphs, encodes literals, and minifies the source. It also shuffles independent declarations and rewrites branches using native Python control flow. By default it adds irregular indentation and spacing. The output is a standalone Python file.

## Usage

```sh
python -m pip install -r requirements.txt
python obfusbaker.py examples/telemetry/source.py -o obfuscated.py
python obfuscated.py
```

Use `--no-indent` for regular indentation and `--keep NAME` to preserve a name that callers depend on. Run `python obfusbaker.py --help` for all options.

Each folder in [examples](examples/) contains the original program and its generated output.

<img src="examples/bindings/comparison.png" alt="Bindings source beside its no-indent obfuscation, with long obfuscated lines cropped" width="850">

## Slowdowns

Median runtime including Python startup over 21 runs per build on CPython 3.13.15.

| Example | Original | Obfuscated |
| --- | ---: | ---: |
| Generators | 9.3 ms | 10.1 ms (1.08×) |
| Telemetry (200,000 readings) | 29.4 ms | 50.0 ms (1.70×) |
| N-Queens (10 queens) | 107.2 ms | 286.9 ms (2.68×) |

As a rough guide, budget 0–15% extra runtime for scripts dominated by I/O or library calls. Tight Python loops with frequent attribute access or comparisons can take 1.5–3× as long.

## Development

Development is not active. I only intend to update this project when needed.

---

## Copyright and License
© [Vinyzu](https://github.com/Vinyzu/)

[GNU GPL](https://choosealicense.com/licenses/gpl-3.0/)

(Commercial Usage is allowed, but source, license and copyright has to made available. Obfusbaker does not provide and Liability or Warranty)

---

## Thanks to

[SvenSkiTheSource](https://github.com/Svenskithesource) (For sharing his Obfuscating Knowledge)

---

![Version](https://img.shields.io/badge/Obfuscator-v3.0-blue)
![License](https://img.shields.io/badge/License-GNU%20GPL-green)
![Python](https://img.shields.io/badge/Python-v3.10%2B-lightgrey)

[![my-discord](https://img.shields.io/badge/My_Discord-000?style=for-the-badge&logo=google-chat&logoColor=blue)](https://discordapp.com/users/935224495126487150)
[![buy-me-a-coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-000?style=for-the-badge&logo=ko-fi&logoColor=brown)](https://ko-fi.com/vinyzu)
