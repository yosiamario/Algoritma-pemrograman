"""
╔══════════════════════════════════════════════════════════════════════╗
║          KNIGHT'S TOUR PROBLEM — Algoritma Backtracking             ║
║          Perjalanan Kuda Catur Mengunjungi Semua Kotak              ║
╚══════════════════════════════════════════════════════════════════════╝

Deskripsi:
    Kuda catur (knight) harus mengunjungi setiap kotak pada papan NxN
    TEPAT SATU KALI menggunakan gerakan L-shape khas kuda catur.

Fitur:
    • Backtracking murni dengan Warnsdorff's Heuristic (smart ordering)
    • Visualisasi animasi papan real-time di CLI
    • Penanda urutan kunjungan tiap kotak
    • Statistik langkah, backtrack, dan waktu eksekusi
    • Mode: animasi penuh / cepat / multi-start (cari dari semua posisi)
    • Ekspor solusi ke file .txt
"""

import time
import os
import sys

# ─── ANSI Colors ───────────────────────────────────────────
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m";  DIM     = "\033[2m"
    RED     = "\033[91m"; GREEN   = "\033[92m"; YELLOW  = "\033[93m"
    BLUE    = "\033[94m"; MAGENTA = "\033[95m"; CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_GRN  = "\033[42m"; BG_BLU  = "\033[44m"; BG_YLW  = "\033[43m"
    BG_RED  = "\033[41m"; BG_DRK  = "\033[100m"

# ─── 8 kemungkinan gerakan kuda (dx, dy) ──────────────────
MOVES = [
    (-2, -1), (-2, +1),
    (-1, -2), (-1, +2),
    (+1, -2), (+1, +2),
    (+2, -1), (+2, +1),
]

# ─── Statistik global ──────────────────────────────────────
class Stats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.steps      = 0
        self.backtracks = 0
        self.start_time = 0.0
        self.solution: list[list[int]] | None = None   # board berisi urutan


STATS = Stats()

# ─── Utilitas ──────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header():
    print(f"\n{C.BG_BLU}{C.BOLD}{'':^62}{C.RESET}")
    print(f"{C.BG_BLU}{C.BOLD}{'  KNIGHT\'S TOUR — BACKTRACKING':^62}{C.RESET}")
    print(f"{C.BG_BLU}{C.BOLD}{'':^62}{C.RESET}\n")


def is_valid(board: list[list[int]], row: int, col: int, n: int) -> bool:
    """Cek apakah (row, col) berada di dalam papan dan belum dikunjungi."""
    return 0 <= row < n and 0 <= col < n and board[row][col] == -1


# ─── Warnsdorff's Heuristic ────────────────────────────────

def warnsdorff_score(board: list[list[int]], row: int, col: int, n: int) -> int:
    """
    Hitung jumlah langkah valid yang tersedia dari (row, col).
    Digunakan untuk mengurutkan kandidat: lebih sedikit pilihan = dicoba duluan.
    Ini adalah heuristik Warnsdorff yang secara dramatis mengurangi backtrack.
    """
    count = 0
    for dr, dc in MOVES:
        nr, nc = row + dr, col + dc
        if is_valid(board, nr, nc, n):
            count += 1
    return count


def get_candidates(board: list[list[int]], row: int, col: int,
                   n: int, use_heuristic: bool) -> list[tuple[int, int]]:
    """
    Kembalikan daftar langkah valid dari (row, col).
    Jika use_heuristic=True, urutkan dengan Warnsdorff (ascending score).
    """
    candidates = []
    for dr, dc in MOVES:
        nr, nc = row + dr, col + dc
        if is_valid(board, nr, nc, n):
            candidates.append((nr, nc))

    if use_heuristic:
        candidates.sort(key=lambda pos: warnsdorff_score(board, pos[0], pos[1], n))

    return candidates


# ─── Tampilan papan ────────────────────────────────────────

def render_board(board: list[list[int]], n: int,
                 cur_row: int, cur_col: int, move_num: int,
                 label: str = ""):
    """Cetak papan dengan warna."""
    # Header kolom
    col_labels = "     " + "  ".join(
        f"{C.DIM}{chr(65 + c)}{C.RESET}" for c in range(n)
    )
    print(col_labels)

    for r in range(n):
        # Nomor baris
        row_str = f"  {C.DIM}{r + 1:2}{C.RESET} "
        for c in range(n):
            val = board[r][c]
            is_current = (r == cur_row and c == cur_col)
            is_light   = (r + c) % 2 == 0   # kotak terang/gelap

            if is_current:
                cell = f"{C.BG_YLW}{C.BOLD}{C.BLACK if hasattr(C,'BLACK') else ''}" \
                       f" {val:2}{C.RESET}"
            elif val != -1:
                shade = C.BG_GRN if is_light else C.BG_DRK
                txt   = C.BOLD + C.WHITE
                cell  = f"{shade}{txt} {val:2}{C.RESET}"
            else:
                shade = "\033[48;5;250m" if is_light else "\033[48;5;240m"
                cell  = f"{shade}   {C.RESET}"

            row_str += cell
        print(row_str)

    elapsed = time.time() - STATS.start_time
    print(f"\n  {C.DIM}Langkah: {C.YELLOW}{STATS.steps:<6}{C.RESET}"
          f"  {C.DIM}Backtrack: {C.RED}{STATS.backtracks:<5}{C.RESET}"
          f"  {C.DIM}Gerakan: {C.CYAN}{move_num}/{n*n}{C.RESET}"
          f"  {C.DIM}[{elapsed:.2f}s]{C.RESET}")
    if label:
        print(f"  {label}")
    print()


# ─── Backtracking ──────────────────────────────────────────

def backtrack(board: list[list[int]], row: int, col: int,
              move_num: int, n: int,
              use_heuristic: bool, animate: bool, delay: float) -> bool:
    """
    Rekursif backtracking Knight's Tour.
    board[r][c] = urutan kunjungan (1-based), -1 = belum dikunjungi.
    """
    STATS.steps += 1

    if animate:
        clear()
        header()
        render_board(board, n, row, col, move_num,
                     label=f"{C.CYAN}Menempatkan gerakan ke-{move_num} "
                           f"di ({row+1},{chr(65+col)}){C.RESET}")
        time.sleep(delay)

    # Base case: semua kotak sudah dikunjungi
    if move_num == n * n:
        STATS.solution = [row[:] for row in board]
        return True

    # Dapatkan kandidat gerakan berikutnya
    candidates = get_candidates(board, row, col, n, use_heuristic)

    for nr, nc in candidates:
        board[nr][nc] = move_num + 1
        result = backtrack(board, nr, nc, move_num + 1,
                           n, use_heuristic, animate, delay)
        if result:
            return True

        # Backtrack
        board[nr][nc] = -1
        STATS.backtracks += 1

        if animate:
            clear()
            header()
            render_board(board, n, row, col, move_num,
                         label=f"{C.RED}↩ Backtrack dari "
                               f"({nr+1},{chr(65+nc)}) → "
                               f"({row+1},{chr(65+col)}){C.RESET}")
            time.sleep(delay * 0.5)

    return False


# ─── Mode Multi-Start ──────────────────────────────────────

def multi_start_search(n: int, use_heuristic: bool) -> list[tuple[int,int,float]]:
    """
    Coba semua posisi awal (0,0) s.d. (n-1,n-1).
    Kembalikan list (start_row, start_col, waktu_eksekusi) yang berhasil.
    """
    results = []
    total   = n * n
    print(f"\n  {C.BOLD}Mencari dari semua {total} posisi awal "
          f"(N={n})...{C.RESET}\n")

    for sr in range(n):
        for sc in range(n):
            board = [[-1] * n for _ in range(n)]
            board[sr][sc] = 1
            STATS.reset()
            STATS.start_time = time.time()

            found = backtrack(board, sr, sc, 1, n, use_heuristic,
                              animate=False, delay=0)
            elapsed = time.time() - STATS.start_time

            status = f"{C.GREEN}✔{C.RESET}" if found else f"{C.RED}✘{C.RESET}"
            print(f"  Start ({sr+1},{chr(65+sc)})  {status}  "
                  f"steps={C.YELLOW}{STATS.steps:<7}{C.RESET}  "
                  f"backtracks={C.RED}{STATS.backtracks:<6}{C.RESET}  "
                  f"[{elapsed:.3f}s]")

            if found:
                results.append((sr, sc, elapsed))

    return results


# ─── Tampilkan solusi akhir ────────────────────────────────

def print_solution(n: int, start_r: int, start_c: int):
    if STATS.solution is None:
        print(f"\n  {C.BG_RED}{C.BOLD}  Tidak ada solusi ditemukan!  {C.RESET}\n")
        return

    elapsed = time.time() - STATS.start_time
    board   = STATS.solution

    clear()
    header()
    print(f"  {C.BG_GRN}{C.BOLD}{'  SOLUSI DITEMUKAN!':^48}{C.RESET}\n")
    render_board(board, n, -1, -1, n * n)

    print(f"  {C.BOLD}Papan        : {C.RESET}{n} x {n} "
          f"({n*n} kotak)")
    print(f"  {C.BOLD}Start        : {C.RESET}baris {start_r+1}, "
          f"kolom {chr(65+start_c)}")
    print(f"  {C.BOLD}Total langkah: {C.YELLOW}{STATS.steps}{C.RESET}")
    print(f"  {C.BOLD}Backtracks   : {C.RED}{STATS.backtracks}{C.RESET}")
    print(f"  {C.BOLD}Waktu        : {C.WHITE}{elapsed:.4f} detik{C.RESET}\n")

    # Rekonstruksi urutan gerakan
    order = [None] * (n * n)
    for r in range(n):
        for c in range(n):
            order[board[r][c] - 1] = (r, c)

    print(f"  {C.BOLD}Urutan gerakan kuda:{C.RESET}")
    for i in range(0, n * n, 8):
        chunk = order[i:i+8]
        parts = "  →  ".join(
            f"{C.CYAN}({r+1},{chr(65+c)}){C.RESET}" for r, c in chunk
        )
        print(f"  {parts}")
    print()


def export_solution(n: int, start_r: int, start_c: int):
    if STATS.solution is None:
        return
    board   = STATS.solution
    elapsed = time.time() - STATS.start_time
    fname   = f"knights_tour_{n}x{n}_{start_r+1}{chr(65+start_c)}.txt"

    order = [None] * (n * n)
    for r in range(n):
        for c in range(n):
            order[board[r][c] - 1] = (r, c)

    with open(fname, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("  KNIGHT'S TOUR — HASIL SOLUSI\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Papan        : {n} x {n}\n")
        f.write(f"Posisi awal  : baris {start_r+1}, kolom {chr(65+start_c)}\n")
        f.write(f"Total langkah: {STATS.steps}\n")
        f.write(f"Backtracks   : {STATS.backtracks}\n")
        f.write(f"Waktu        : {elapsed:.4f} detik\n\n")
        f.write("Papan (angka = urutan kunjungan):\n")
        f.write("     " + "  ".join(chr(65+c) for c in range(n)) + "\n")
        for r in range(n):
            f.write(f"  {r+1}  " + "  ".join(f"{board[r][c]:2}" for c in range(n)) + "\n")
        f.write("\nUrutan gerakan:\n")
        for i, (r, c) in enumerate(order, 1):
            f.write(f"  {i:3}. ({r+1},{chr(65+c)})\n")

    print(f"  {C.GREEN}Diekspor ke: {C.BOLD}{fname}{C.RESET}\n")


# ─── Main ──────────────────────────────────────────────────

def main():
    STATS.reset()
    clear()
    header()

    # ── Pilih ukuran papan
    print(f"  {C.BOLD}{C.CYAN}Ukuran Papan{C.RESET}")
    print(f"  [1] 5 x 5   (mudah)")
    print(f"  [2] 6 x 6   (sedang)")
    print(f"  [3] 8 x 8   (standar catur)")
    print(f"  [4] Custom")
    ch_n = input("\n  Pilih [1/2/3/4]: ").strip()
    n_map = {"1": 5, "2": 6, "3": 8}
    if ch_n in n_map:
        n = n_map[ch_n]
    else:
        while True:
            try:
                n = int(input("  Masukkan N (5-10): "))
                if 5 <= n <= 10:
                    break
                print("  N harus 5-10.")
            except ValueError:
                print("  Input tidak valid.")

    # ── Pilih mode
    print(f"\n  {C.BOLD}{C.CYAN}Mode Pencarian{C.RESET}")
    print(f"  [1] Pilih posisi awal + animasi langkah")
    print(f"  [2] Pilih posisi awal + cepat (tanpa animasi)")
    print(f"  [3] Multi-start: coba semua posisi awal")
    ch_mode = input("\n  Pilih [1/2/3]: ").strip()

    # ── Pilih heuristik
    print(f"\n  {C.BOLD}{C.CYAN}Strategi{C.RESET}")
    print(f"  [1] Warnsdorff's Heuristic (lebih cepat, sedikit backtrack)")
    print(f"  [2] Brute-force (tanpa heuristik, murni backtracking)")
    ch_h = input("\n  Pilih [1/2]: ").strip()
    use_heuristic = (ch_h != "2")

    # ── Mode 3: multi-start
    if ch_mode == "3":
        STATS.start_time = time.time()
        results = multi_start_search(n, use_heuristic)
        print(f"\n  {C.BOLD}Posisi yang berhasil: {C.GREEN}{len(results)}{C.RESET}"
              f" dari {n*n} posisi awal\n")
        return

    # ── Mode 1 / 2: satu posisi awal
    print(f"\n  {C.BOLD}{C.CYAN}Posisi Awal Kuda{C.RESET}")
    print(f"  Baris 1-{n}, Kolom A-{chr(64+n)}")

    while True:
        try:
            sr = int(input(f"  Baris (1-{n}): ")) - 1
            if 0 <= sr < n:
                break
        except ValueError:
            pass
        print("  Input tidak valid.")

    while True:
        sc_raw = input(f"  Kolom (A-{chr(64+n)}): ").strip().upper()
        sc = ord(sc_raw) - 65
        if 0 <= sc < n:
            break
        print("  Input tidak valid.")

    animate = (ch_mode == "1")
    delay   = 0.0
    if animate:
        try:
            delay = float(input("  Kecepatan animasi detik/langkah (0.05-1.0, default=0.2): ") or "0.2")
        except ValueError:
            delay = 0.2

    # ── Jalankan backtracking
    board = [[-1] * n for _ in range(n)]
    board[sr][sc] = 1

    clear()
    header()
    print(f"  Mencari Knight's Tour pada papan {n}x{n}...")
    print(f"  Start: baris {sr+1}, kolom {chr(65+sc)}")
    print(f"  Heuristik: {'Warnsdorff' if use_heuristic else 'Brute-force'}\n")
    if not animate:
        print(f"  {C.DIM}Mohon tunggu...{C.RESET}")

    STATS.start_time = time.time()
    found = backtrack(board, sr, sc, 1, n, use_heuristic, animate, delay)

    print_solution(n, sr, sc)

    if found:
        raw_e = input("  Ekspor solusi ke file .txt? (y/n): ").strip().lower()
        if raw_e == "y":
            export_solution(n, sr, sc)

    raw_r = input("  Coba lagi? (y/n): ").strip().lower()
    if raw_r == "y":
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Program dihentikan.{C.RESET}\n")
        sys.exit(0)
