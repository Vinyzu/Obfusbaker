# Obfusbaker v2.0
Obfusbaker is a Python Obfuscator.
It doesnt use exec() or eval() to run hashed/encrypted python code from strings.
It renames Variables, Functions and Builtins in misc. UniCode Chars to break an IDE/Code Editor.
It also encrypts strings in a custom encryption function, minifies the code and by default adds random indentations to further disable visibility for a potential code breaker.
You can also choose the maximum Protection Option, in which Obfusbaker obfuscates attribute names, by wrapping them inside setattr() and getattr() functions.

## Slowdowns
Because Obfusbaker messes with the Source Code and adds Protection algorithm, it produces slowdowns for your code.
The Example Times for a very calculation heavy task (N-Queens solver with dancing links) are:

|    Obfuscation Type   | Time for Execution | Slowdown by |
|:---------------------:|:------------------:|:-----------:|
|     No Obfuscation    | 0.4332432746887207 |     1x      |
|  Default Obfuscation  | 1.7924633026123047 |     4x      |
| No Indent Obfuscation | 1.2777245044708252 |     3x      |
|  Maximum Obfuscation  | 10.297466278076172 |     23x     |


Note that these times are measured on a very calculation heavy task.
For normal Python Scripts, you can expect the Slowdowns to be lower.


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

![Version](https://img.shields.io/badge/Obfuscator-v2.0-blue)
![License](https://img.shields.io/badge/License-GNU%20GPL-green)
![Python](https://img.shields.io/badge/Python-v3.x-lightgrey)

[![my-discord](https://img.shields.io/badge/My_Discord-000?style=for-the-badge&logo=google-chat&logoColor=blue)](https://discordapp.com/users/935224495126487150)
[![buy-me-a-coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-000?style=for-the-badge&logo=ko-fi&logoColor=brown)](https://ko-fi.com/vinyzu)