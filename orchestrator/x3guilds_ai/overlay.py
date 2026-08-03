from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Literal

from x3guilds_ai.models import (
    BridgeError,
    ChatRequest,
    ContextSelection,
    DialogueResponse,
)


@dataclass(slots=True)
class OverlayEvent:
    kind: Literal["request", "response", "error", "status", "context"]
    speaker: str
    text: str
    mood: str = "neutral"


@dataclass(slots=True)
class OverlaySubmission:
    context: ContextSelection
    message: str


class OverlayEventQueue:
    def __init__(self) -> None:
        self._events: queue.Queue[OverlayEvent] = queue.Queue()
        self._submissions: queue.Queue[OverlaySubmission] = queue.Queue()
        self._context: ContextSelection | None = None
        self._lock = threading.Lock()

    def put(self, event: OverlayEvent) -> None:
        self._events.put(event)

    def drain(self) -> list[OverlayEvent]:
        events: list[OverlayEvent] = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                return events

    def active_context(self) -> ContextSelection | None:
        with self._lock:
            return self._context.model_copy(deep=True) if self._context else None

    def context_callback(self, context: ContextSelection) -> None:
        with self._lock:
            self._context = context.model_copy(deep=True)
        details = " · ".join(
            value
            for value in [context.entity.kind, context.entity.race, context.entity.sector]
            if value
        )
        self.put(
            OverlayEvent(
                "context",
                "Канал выбран",
                f"{context.entity.name}{' · ' + details if details else ''}",
            )
        )

    def submit(self, message: str) -> bool:
        cleaned = message.strip()
        if not cleaned:
            return False
        context = self.active_context()
        if context is None:
            self.put(OverlayEvent("error", "Система связи", "Сначала выберите цель в X3FL."))
            return False
        self._submissions.put(OverlaySubmission(context=context, message=cleaned))
        return True

    def drain_submissions(self) -> list[OverlaySubmission]:
        items: list[OverlaySubmission] = []
        while True:
            try:
                items.append(self._submissions.get_nowait())
            except queue.Empty:
                return items

    def bridge_callback(
        self,
        request: ChatRequest,
        result: DialogueResponse | BridgeError,
    ) -> None:
        self.put(OverlayEvent("request", "Игрок", request.message))
        if isinstance(result, DialogueResponse):
            self.put(
                OverlayEvent(
                    "response",
                    request.entity.name,
                    result.reply,
                    result.mood,
                )
            )
        else:
            self.put(
                OverlayEvent(
                    "error",
                    "Система связи",
                    f"{result.code}: {result.message}",
                )
            )


class ChatOverlay:
    def __init__(
        self,
        *,
        events: OverlayEventQueue,
        width: int,
        height: int,
        always_on_top: bool,
        on_close,
    ) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._events = events
        self._on_close = on_close
        self.root = tk.Tk()
        self.root.title("X3 Guilds · Живая связь")
        self.root.geometry(f"{width}x{height}+40+80")
        self.root.minsize(420, 300)
        self.root.attributes("-topmost", always_on_top)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        frame = ttk.Frame(self.root, padding=8)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x")
        self.status = ttk.Label(header, text="В X3FL выберите объект и нажмите горячую клавишу")
        self.status.pack(side="left", fill="x", expand=True)
        ttk.Button(header, text="Скрыть", command=self.root.iconify).pack(side="right")

        self.transcript = tk.Text(
            frame,
            wrap="word",
            state="disabled",
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self.transcript.pack(fill="both", expand=True, pady=(8, 8))
        self.transcript.tag_configure("speaker", font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("error", foreground="#b00020")
        self.transcript.tag_configure("system", foreground="#666666")

        composer = ttk.Frame(frame)
        composer.pack(fill="x")
        self.message = ttk.Entry(composer)
        self.message.pack(side="left", fill="x", expand=True)
        self.message.bind("<Return>", self._send)
        ttk.Button(composer, text="Передать", command=self._send).pack(side="right", padx=(8, 0))

        self.root.after(100, self._poll)

    def _send(self, _event=None) -> None:
        message = self.message.get()
        if self._events.submit(message):
            self.message.delete(0, "end")
            self.status.configure(text="Передача сообщения…")

    def _append(self, event: OverlayEvent) -> None:
        self.transcript.configure(state="normal")
        tag = "error" if event.kind == "error" else ("system" if event.kind in {"status", "context"} else "speaker")
        self.transcript.insert("end", f"{event.speaker}\n", tag)
        self.transcript.insert("end", f"{event.text}\n\n")
        self.transcript.see("end")
        self.transcript.configure(state="disabled")
        if event.kind == "response":
            self.status.configure(text=f"Ответ: {event.speaker} · настроение: {event.mood}")
        elif event.kind == "error":
            self.status.configure(text="Ошибка канала связи")
        elif event.kind == "context":
            self.status.configure(text=f"Активная связь: {event.text}")
            self.message.focus_set()
        elif event.kind == "status":
            self.status.configure(text=event.text)
        else:
            self.status.configure(text="Ожидание ответа…")

    def _poll(self) -> None:
        for event in self._events.drain():
            self._append(event)
        self.root.after(100, self._poll)

    def close(self) -> None:
        self._on_close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
