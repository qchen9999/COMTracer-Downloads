# COMTracer

COMTracer is a Windows x64 utility from BBSoft LLC for tracing COM interface methods, Automation calls and optional imported DLL function calls.

[Product page and getting started](https://www.bbsoftllc.com/comtracer/) · [Latest release](https://github.com/qchen9999/COMTracer-Downloads/releases/latest)

## Downloads

Use the signed MSI installer or extract the portable ZIP and run COMTracer.exe. Keep the executable and hook DLL together. Windows 10 version 1709 or newer and native x64 target processes are required.

The executable, tracing DLL, demo and MSI carry timestamped BBSOFT LLC signatures. Each release includes SHA-256 checksums, signature receipts and build information. Compare your downloaded package with SHA256SUMS.txt before use.

## Features

- COM method arguments and return values when supported signatures are available.
- Automatic embedded type-library discovery and .tlb/.olb imports for custom interfaces.
- Automation member names, friendly interface IDs, a type-library browser and optional stacks.
- Optional entry-only tracing of regular DLL imports, delay-loaded functions and executable exports resolved through GetProcAddress.
- Live filtering, JSONL export, system tray capture and clean detach.

Capture depends on observed interfaces and available signatures. DLL function tracing does not guess argument types or intercept returns. Previously obtained function pointers and custom export resolvers are outside this mode; see the included README for details.

This repository distributes official release files and documentation. It does not contain the application source code.

Support: support@bbsoftllc.com
