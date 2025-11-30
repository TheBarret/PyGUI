# PyGui
A Lightweight, Message-Driven GUI Framework for PyGame (WIP)  
*Inspired by the PyGame community — built to contribute back.*

<img width="1002" height="632" alt="image" src="https://github.com/user-attachments/assets/54f3f904-4362-404b-9118-a34a105ff789" />

The gui is a minimal, component-based framework built exclusively for PyGame (Python 3.10+). Designed from the ground up for clarity and extensibility, it provides windowing, layout, theming, and event handling — without external dependencies.  

## Core Principles

- **Atomic Components**: objects are composable, hierarchical, and self-contained.
- **Messaging**: The `AddressBus` enables broadcast/request-response communication for runtime introspection and control.
- **Theme**: Centralized visual appearance  in `Theme`, not very advanced just basics.
- **Event Propagation**: Reverse-Z-order event bubbling with focus management, passthrough, and hover/click/keypress handling.

## Components

- `Container`
- `Window`
- `Label`
- `MultiLabel`
- `Button`
- `Icon`




