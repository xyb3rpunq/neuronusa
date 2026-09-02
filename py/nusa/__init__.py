"""Mesin neuronusa: algoritma kecerdasan buatan yang berjalan di peramban.

Seluruh modul di sini dijalankan dua kali — CPython saat uji dan konformansi,
Brython di dalam peramban. Karena itu tidak satu pun memakai pustaka di luar
yang tersedia di keduanya: hanya ``math``.

Jangan menambahkan ``numpy``, ``decimal``, atau ``random`` ke modul mana pun di
paket ini. Ketiganya tidak tersedia penuh di Brython, dan kegagalannya baru
terlihat saat halamannya dibuka — bukan saat ujinya dijalankan.

.Deckyx
"""

__all__ = ["fx", "inti", "jaringan"]
