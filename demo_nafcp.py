# -*- coding: utf-8 -*-
"""
ĐỒ ÁN MÔN DATAMINING
SỬ DỤNG THUẬT TOÁN NAFCP TRONG VIỆC KHAI THÁC TẬP PHỔ BIẾN ĐÓNG
Nhóm 04: Thành viên: Nguyễn Phi Nhung, Lê Bảo Trâm, Hồ Đăng Tuệ
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

class Node:
    def __init__(self, item, parent=None):
        self.item = item
        self.parent = parent
        self.children = {}
        self.frequency = 0
        self.pre_order = 0
        self.post_order = 0

class PPCTree:
    def __init__(self, transactions, min_sup):
        self.root = Node(None)
        self.header_table = {}
        self.item_order = []
        self.min_sup = min_sup
        self.transactions = transactions
        self.counter = [1, 1]  # pre-order, post-order counter
        
        self._find_frequent_items()
        self._build_tree()
        self._assign_orders(self.root)

    def _find_frequent_items(self):
        item_counts = {}
        for transaction in self.transactions:
            for item in transaction:
                item_counts[item] = item_counts.get(item, 0) + 1
                
        self.frequent_items = [item for item, count in item_counts.items() 
                              if count >= self.min_sup]
        self.frequent_items.sort(key=lambda x: (-item_counts[x], x))
        self.item_order = {item: idx for idx, item in enumerate(self.frequent_items)}
        
    def _build_tree(self):
        for transaction in self.transactions:
            filtered = [item for item in transaction if item in self.frequent_items]
            filtered.sort(key=lambda x: self.item_order[x])
            self._insert(filtered, self.root)
            
    def _insert(self, items, parent):
        if not items:
            return
        first = items[0]
        if first in parent.children:
            node = parent.children[first]
            node.frequency += 1
        else:
            node = Node(first, parent)
            node.frequency = 1
            parent.children[first] = node
            if first not in self.header_table:
                self.header_table[first] = []
            self.header_table[first].append(node)
        self._insert(items[1:], node)
        
    def _assign_orders(self, node):
        if node.item is not None:
            node.pre_order = self.counter[0]
            self.counter[0] += 1
        for child in node.children.values():
            self._assign_orders(child)
        if node.item is not None:
            node.post_order = self.counter[1]
            self.counter[1] += 1

class NAFCP:
    def __init__(self, transactions, min_sup):
        print(f"Khởi tạo NAFCP với ngưỡng tối thiểu = {min_sup}")
        self.min_sup = min_sup
        self.ppc_tree = PPCTree(transactions, min_sup)
        self.n_lists = {}
        self.patterns = {}
        self._build_nlists()

    def _build_nlists(self):
        print("Xây dựng N-list cho các mục 1-item phổ biến")
        for item in self.ppc_tree.frequent_items:
            nl = []
            for node in self.ppc_tree.header_table.get(item, []):
                nl.append({'pre': node.pre_order, 'post': node.post_order, 'freq': node.frequency})
            self.n_lists[item] = nl
            print(f"  N-list[{item}] = {nl}")

    def _intersect(self, nl1, nl2):
        result = []
        i = j = 0
        while i < len(nl1) and j < len(nl2):
            if nl1[i]['pre'] < nl2[j]['pre'] and nl1[i]['post'] > nl2[j]['post']:
                freq = min(nl1[i]['freq'], nl2[j]['freq'])
                result.append({'pre': nl1[i]['pre'], 'post': nl1[i]['post'], 'freq': freq})
                j += 1
            elif nl1[i]['pre'] < nl2[j]['pre']:
                i += 1
            else:
                j += 1
        return result

    def _get_support(self, nlist):
        return sum(entry['freq'] for entry in nlist)

    def mine(self):
        print("Bắt đầu quá trình khai thác mẫu...")
        items = self.ppc_tree.frequent_items
        for idx in range(len(items)-1, -1, -1):
            item = items[idx]
            nl = self.n_lists[item]
            sup = self._get_support(nl)
            print(f"Xét mục cơ sở {item}, độ hỗ trợ = {sup}")
            if sup >= self.min_sup:
                self.patterns[(item,)] = sup
                print(f"  Thêm mẫu {(item,)}")
                self._enumerate([item], nl, items[:idx])
        print("Hoàn thành liệt kê, đang lọc các mẫu đóng...")
        fcps = []
        for pat, sup in self.patterns.items():
            print(f"Kiểm tra xem mẫu {pat} có đóng không")
            is_closed = True
            for other, sup_o in self.patterns.items():
                if set(pat) < set(other) and sup_o == sup:
                    print(f"  {pat} không đóng, tập siêu {other} có cùng độ hỗ trợ {sup_o}")
                    is_closed = False
                    break
            if is_closed:
                print(f"  {pat} là mẫu đóng; giữ lại")
                fcps.append((list(pat), sup))
        print("Khai thác hoàn tất. Danh sách FCP cuối cùng:")
        return sorted(fcps, key=lambda x: (-len(x[0]), x[0]))

    def _enumerate(self, prefix, prefix_nl, suffix_items):
        print(f"Đang liệt kê tiền tố {prefix}, hậu tố {suffix_items}")
        for idx in range(len(suffix_items)-1, -1, -1):
            item = suffix_items[idx]
            nl = self.n_lists[item]
            merged_nl = self._intersect(nl, prefix_nl)
            sup = self._get_support(merged_nl)
            print(f"  Thử mở rộng {prefix} + [{item}] => độ hỗ trợ {sup}")
            if sup >= self.min_sup:
                merged = sorted(prefix + [item], key=lambda x: self.ppc_tree.item_order[x])
                print(f"    Thêm mẫu {tuple(merged)} với độ hỗ trợ {sup}")
                self.patterns[tuple(merged)] = sup
                self._enumerate(merged, merged_nl, suffix_items[:idx])
class NAFCP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Phần mềm khai thác FCP bằng NAFCP")
        self.root.geometry("800x700")
        self.root.configure(bg="#f4f4f4")  

        # Style chung
        label_font = ("Arial", 11, "bold")
        entry_font = ("Arial", 11)
        btn_font = ("Arial", 11, "bold")

        # Label: Hướng dẫn nhập giao dịch
        self.input_label = tk.Label(root, text="Nhập giao dịch (mỗi dòng 1 giao dịch, cách nhau bởi dấu phẩy):",
                                    font=label_font, bg="#f4f4f4", fg="#333")
        self.input_label.pack(padx=10, pady=(15, 0), anchor="w")

        # Vùng nhập liệu
        self.text_area = ScrolledText(root, height=10, font=entry_font, bg="#fffaf0", fg="#000")
        self.text_area.pack(padx=10, pady=5, fill='x')

        # Nút tải file
        self.load_button = tk.Button(root, text="📂 Tải file giao dịch", command=self.load_file,
                                     font=btn_font, bg="#4CAF50", fg="white", activebackground="#45a049")
        self.load_button.pack(pady=8)

        # Nhập ngưỡng hỗ trợ
        self.min_sup_label = tk.Label(root, text="Ngưỡng hỗ trợ tối thiểu:", font=label_font, bg="#f4f4f4", fg="#333")
        self.min_sup_label.pack(padx=10, anchor="w")

        self.min_sup_entry = tk.Entry(root, font=entry_font, bg="#fff")
        self.min_sup_entry.pack(padx=10, pady=3, fill='x')

        # Nút khai thác
        self.mine_button = tk.Button(root, text="🚀 Khai thác FCP", command=self.mine_fcps,
                                     font=btn_font, bg="#2196F3", fg="white", activebackground="#1976D2")
        self.mine_button.pack(pady=(10, 5))

        # Nút làm mới
        self.reset_button = tk.Button(root, text="🔄 Làm mới", command=self.reset_fields,
                                      font=btn_font, bg="#f44336", fg="white", activebackground="#d32f2f")
        self.reset_button.pack(pady=(0, 10))

        # Kết quả
        self.result_label = tk.Label(root, text="📊 Kết quả khai thác FCP:", font=label_font, bg="#f4f4f4", fg="#333")
        self.result_label.pack(padx=10, pady=(10, 0), anchor="w")

        self.result_area = ScrolledText(root, height=15, font=("Courier New", 11), bg="#f9f9f9", fg="#000")
        self.result_area.pack(padx=10, pady=5, fill='both', expand=True)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Text & CSV Files", "*.txt *.csv"),
            ("All Files", "*.*")
        ])
        if file_path:
            try:
                import csv
                lines = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith(".csv"):
                        reader = csv.reader(f)
                        for row in reader:
                            clean_row = [item.strip() for item in row if item.strip()]
                            if clean_row:
                                lines.append(",".join(clean_row))
                    else:
                        for line in f:
                            line = line.strip().strip('"')
                            if line:
                                lines.append(line)
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert(tk.END, "\n".join(lines))
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")


    def mine_fcps(self):
        raw_data = self.text_area.get('1.0', tk.END).strip()
        min_sup_str = self.min_sup_entry.get()

        if not raw_data or not min_sup_str:
            messagebox.showerror("Lỗi", "Vui lòng nhập giao dịch và ngưỡng hỗ trợ!")
            return
        try:
            min_sup = int(min_sup_str)
        except ValueError:
            messagebox.showerror("Lỗi", "Ngưỡng hỗ trợ phải là số nguyên!")
            return

        transactions = []
        for line in raw_data.splitlines():
            items = [item.strip() for item in line.split(',') if item.strip()]
            if items:
                transactions.append(items)

        nafcp = NAFCP(transactions, min_sup)
        fcps = nafcp.mine()

        self.result_area.delete('1.0', tk.END)
        for pat, sup in fcps:
            self.result_area.insert(tk.END, f"{pat} (Độ hỗ trợ: {sup})\n")

    def reset_fields(self):
        self.text_area.delete('1.0', tk.END)
        self.min_sup_entry.delete(0, tk.END)
        self.result_area.delete('1.0', tk.END)


# -----------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = NAFCP_GUI(root)
    root.mainloop()
