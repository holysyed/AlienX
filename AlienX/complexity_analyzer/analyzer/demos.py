"""
analyzer/demos.py
──────────────────
Built-in demo snippets users can load with the 'demo' command.
"""

from __future__ import annotations

DEMOS: dict[str, tuple[str, str]] = {
    "1": (
        "python",
        """\
# Bubble Sort — O(n²)
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
""",
    ),
    "2": (
        "python",
        """\
# Binary Search — O(log n)
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
""",
    ),
    "3": (
        "python",
        """\
# Merge Sort — O(n log n)
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
""",
    ),
    "4": (
        "python",
        """\
# Naive Fibonacci — O(2^n)  (exponential without memoization)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
""",
    ),
    "5": (
        "python",
        """\
# Three nested loops — O(n³)
def triple_sum(arr, target):
    n = len(arr)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if arr[i] + arr[j] + arr[k] == target:
                    return (i, j, k)
    return None
""",
    ),
    "6": (
        "cpp",
        """\
// Quick Sort — C++ implementation
#include <vector>
using namespace std;

int partition(vector<int>& arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(arr[i], arr[j]);
        }
    }
    swap(arr[i + 1], arr[high]);
    return i + 1;
}

void quick_sort(vector<int>& arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quick_sort(arr, low, pi - 1);
        quick_sort(arr, pi + 1, high);
    }
}
""",
    ),
}


DEMO_MENU = """\
[bold bright_cyan]Built-in Demo Snippets[/bold bright_cyan]

  [yellow]1[/yellow]  Bubble Sort       (Python)  -- O(n^2)
  [yellow]2[/yellow]  Binary Search     (Python)  -- O(log n)
  [yellow]3[/yellow]  Merge Sort        (Python)  -- O(n log n)
  [yellow]4[/yellow]  Fibonacci naive   (Python)  -- O(2^n)
  [yellow]5[/yellow]  Triple Sum loops  (Python)  -- O(n^3)
  [yellow]6[/yellow]  Quick Sort        (C++)      -- O(n^2) worst

Enter number (or anything else to cancel): \
"""
