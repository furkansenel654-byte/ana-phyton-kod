"""
İŞLETİM SİSTEMLERİ - ÖDEV 1
CPU Zamanlama Algoritmaları Simülatörü

Bu modül 6 farklı CPU zamanlama algoritmasını içerir:
1. FCFS (First Come First Served)
2. Preemptive SJF (Shortest Job First)
3. Non-Preemptive SJF
4. Round Robin
5. Preemptive Priority Scheduling
6. Non-Preemptive Priority Scheduling

Yazar: MiniMax Agent
Tarih: 2026
"""

import csv
import threading
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from collections import deque
import copy


@dataclass
class Process:
    """Süreç sınıfı - her sürecin özelliklerini tutar"""
    process_id: str
    arrival_time: int
    burst_time: int
    priority: int
    remaining_time: int = 0
    completion_time: int = 0
    start_time: int = -1
    waiting_time: int = 0
    turnaround_time: int = 0
    is_completed: bool = False
    execution_history: List[Tuple[int, int]] = field(default_factory=list)
    
    def __post_init__(self):
        self.remaining_time = self.burst_time


class CPUScheduler:
    """CPU Zamanlayıcı sınıfı - tüm algoritmaları içerir"""
    
    CONTEXT_SWITCH_TIME = 0.001
    
    def __init__(self, processes: List[Process], quantum: int = 4):
        self.original_processes = processes
        self.quantum = quantum
        self.gantt_chart = []
        self.context_switch_count = 0
        self.total_context_switch_time = 0
        self.results = {}
        
    def reset_simulation(self):
        """Simülasyonu sıfırlar"""
        self.gantt_chart = []
        self.context_switch_count = 0
        self.total_context_switch_time = 0
        self.results = {}
        
    def copy_processes(self) -> List[Process]:
        """Süreçlerin kopyasını oluşturur"""
        return [copy.deepcopy(p) for p in self.original_processes]
    
    def add_to_gantt(self, process_id: str, start: int, end: int):
        """Gantt şemasına veri ekler"""
        self.gantt_chart.append({
            'process': process_id,
            'start': start,
            'end': end,
            'duration': end - start
        })
    
    def add_context_switch(self, current_time: float) -> float:
        """Bağlam değiştirme ekler ve yeni zamanı döndürür"""
        if self.context_switch_count > 0:
            self.gantt_chart.append({
                'process': 'IDLE',
                'start': current_time,
                'end': current_time + self.CONTEXT_SWITCH_TIME,
                'duration': self.CONTEXT_SWITCH_TIME
            })
            current_time += self.CONTEXT_SWITCH_TIME
            self.total_context_switch_time += self.CONTEXT_SWITCH_TIME
        self.context_switch_count += 1
        return current_time
    
    def calculate_metrics(self, processes: List[Process], total_time: float) -> Dict[str, Any]:
        """Metrikleri hesaplar"""
        waiting_times = [p.waiting_time for p in processes]
        turnaround_times = [p.turnaround_time for p in processes]
        
        # Throughput hesaplama (T=50, 100, 150, 200 için)
        throughput = {}
        for t in [50, 100, 150, 200]:
            completed = sum(1 for p in processes if p.completion_time <= t)
            throughput[t] = completed
        
        # CPU verimliliği hesaplama
        total_burst = sum(p.burst_time for p in processes)
        cpu_utilization = (total_burst / total_time) * 100 if total_time > 0 else 0
        
        return {
            'gantt_chart': self.gantt_chart,
            'max_waiting_time': max(waiting_times),
            'avg_waiting_time': sum(waiting_times) / len(waiting_times),
            'max_turnaround_time': max(turnaround_times),
            'avg_turnaround_time': sum(turnaround_times) / len(turnaround_times),
            'throughput': throughput,
            'cpu_utilization': cpu_utilization,
            'context_switch_count': self.context_switch_count,
            'total_context_switch_time': self.total_context_switch_time
        }
    
    # ==================== FCFS ALGORİTMASI ====================
    def fcfs(self) -> Dict[str, Any]:
        """First Come First Served algoritması"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        # Geliş zamanına göre sırala
        processes.sort(key=lambda p: (p.arrival_time, p.process_id))
        
        current_time = 0
        for process in processes:
            # Bağlam değiştirme
            if current_time < process.arrival_time:
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': process.arrival_time,
                    'duration': process.arrival_time - current_time
                })
                current_time = process.arrival_time
            
            current_time = self.add_context_switch(current_time)
            
            # Süreci çalıştır
            process.start_time = current_time
            self.add_to_gantt(process.process_id, current_time, current_time + process.burst_time)
            current_time += process.burst_time
            
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.start_time - process.arrival_time
            process.is_completed = True
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results
    
    # ==================== SJF PREEMPTIVE ====================
    def sjf_preemptive(self) -> Dict[str, Any]:
        """Shortest Job First - Preemptive (Shortest Remaining Time First)"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        current_time = 0
        completed = 0
        total_processes = len(processes)
        
        # Geliş zamanına göre sırala
        processes.sort(key=lambda p: p.arrival_time)
        
        # Kuyrukları oluştur
        ready_queue = []
        arrived_idx = 0
        
        while completed < total_processes:
            # Yeni gelen süreçleri kuyruğa ekle
            while arrived_idx < total_processes and processes[arrived_idx].arrival_time <= current_time:
                ready_queue.append(processes[arrived_idx])
                arrived_idx += 1
            
            if ready_queue:
                # En kısa kalan süreli süreci seç
                ready_queue.sort(key=lambda p: (p.remaining_time, p.arrival_time))
                current_process = ready_queue[0]
                
                current_time = self.add_context_switch(current_time)
                
                # Bir birim çalıştır (veya süreç biterse)
                time_slice = min(1, current_process.remaining_time)
                self.add_to_gantt(current_process.process_id, current_time, current_time + time_slice)
                
                current_process.remaining_time -= time_slice
                current_time += time_slice
                
                if current_process.remaining_time == 0:
                    current_process.completion_time = current_time
                    current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    current_process.is_completed = True
                    completed += 1
                    ready_queue.pop(0)
            else:
                # Hiç süreç yoksa IDLE
                next_arrival = processes[arrived_idx].arrival_time
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': next_arrival,
                    'duration': next_arrival - current_time
                })
                current_time = next_arrival
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results
    
    # ==================== SJF NON-PREEMPTIVE ====================
    def sjf_non_preemptive(self) -> Dict[str, Any]:
        """Shortest Job First - Non-Preemptive"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        current_time = 0
        total_processes = len(processes)
        completed = 0
        
        processes.sort(key=lambda p: p.arrival_time)
        arrived_idx = 0
        completed_processes = []
        
        while completed < total_processes:
            # Mevcut zamana kadar gelen süreçleri bul
            available = []
            for p in processes:
                if not p.is_completed and p.arrival_time <= current_time:
                    available.append(p)
            
            if available:
                # En kısa burst time'a sahip süreci seç
                available.sort(key=lambda p: (p.burst_time, p.arrival_time))
                current_process = available[0]
                
                current_time = self.add_context_switch(current_time)
                
                self.add_to_gantt(current_process.process_id, current_time, current_time + current_process.burst_time)
                current_time += current_process.burst_time
                
                current_process.completion_time = current_time
                current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                current_process.waiting_time = current_process.start_time - current_process.arrival_time if current_process.start_time != -1 else current_time - current_process.arrival_time - current_process.burst_time
                current_process.is_completed = True
                completed += 1
            else:
                # IDLE
                next_arrival = processes[arrived_idx].arrival_time
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': next_arrival,
                    'duration': next_arrival - current_time
                })
                current_time = next_arrival
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results
    
    # ==================== ROUND ROBIN ====================
    def round_robin(self) -> Dict[str, Any]:
        """Round Robin zamanlama algoritması"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        processes.sort(key=lambda p: p.arrival_time)
        
        current_time = 0
        arrived_idx = 0
        ready_queue = deque()
        total_processes = len(processes)
        completed = 0
        
        while completed < total_processes:
            # Yeni süreçleri ekle
            while arrived_idx < total_processes and processes[arrived_idx].arrival_time <= current_time:
                ready_queue.append(processes[arrived_idx])
                arrived_idx += 1
            
            if ready_queue:
                current_process = ready_queue.popleft()
                
                current_time = self.add_context_switch(current_time)
                
                # Quantum veya kalan süre kadar çalıştır
                time_slice = min(self.quantum, current_process.remaining_time)
                self.add_to_gantt(current_process.process_id, current_time, current_time + time_slice)
                
                current_process.remaining_time -= time_slice
                current_time += time_slice
                
                # Yeni süreçleri kuyruğa ekle
                while arrived_idx < total_processes and processes[arrived_idx].arrival_time <= current_time:
                    ready_queue.append(processes[arrived_idx])
                    arrived_idx += 1
                
                if current_process.remaining_time > 0:
                    ready_queue.append(current_process)
                else:
                    current_process.completion_time = current_time
                    current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    current_process.is_completed = True
                    completed += 1
            else:
                # IDLE
                next_arrival = processes[arrived_idx].arrival_time
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': next_arrival,
                    'duration': next_arrival - current_time
                })
                current_time = next_arrival
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results
    
    # ==================== PRIORITY PREEMPTIVE ====================
    def priority_preemptive(self) -> Dict[str, Any]:
        """Priority Scheduling - Preemptive (Düşük öncelik = yüksek öncelikli)"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        current_time = 0
        completed = 0
        total_processes = len(processes)
        
        processes.sort(key=lambda p: p.arrival_time)
        arrived_idx = 0
        ready_queue = []
        
        while completed < total_processes:
            # Yeni gelen süreçleri ekle
            while arrived_idx < total_processes and processes[arrived_idx].arrival_time <= current_time:
                ready_queue.append(processes[arrived_idx])
                arrived_idx += 1
            
            if ready_queue:
                # En yüksek öncelikli süreci seç (düşük sayı = yüksek öncelik)
                ready_queue.sort(key=lambda p: (p.priority, p.arrival_time))
                current_process = ready_queue[0]
                
                current_time = self.add_context_switch(current_time)
                
                # Bir birim çalıştır
                time_slice = min(1, current_process.remaining_time)
                self.add_to_gantt(current_process.process_id, current_time, current_time + time_slice)
                
                current_process.remaining_time -= time_slice
                current_time += time_slice
                
                # Yeni süreçleri ekle
                while arrived_idx < total_processes and processes[arrived_idx].arrival_time <= current_time:
                    ready_queue.append(processes[arrived_idx])
                    arrived_idx += 1
                
                if current_process.remaining_time == 0:
                    current_process.completion_time = current_time
                    current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    current_process.is_completed = True
                    completed += 1
                    ready_queue.pop(0)
            else:
                # IDLE
                next_arrival = processes[arrived_idx].arrival_time
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': next_arrival,
                    'duration': next_arrival - current_time
                })
                current_time = next_arrival
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results
    
    # ==================== PRIORITY NON-PREEMPTIVE ====================
    def priority_non_preemptive(self) -> Dict[str, Any]:
        """Priority Scheduling - Non-Preemptive"""
        self.reset_simulation()
        processes = self.copy_processes()
        
        current_time = 0
        total_processes = len(processes)
        completed = 0
        
        processes.sort(key=lambda p: p.arrival_time)
        arrived_idx = 0
        
        while completed < total_processes:
            # Mevcut zamana kadar gelen süreçleri bul
            available = []
            for p in processes:
                if not p.is_completed and p.arrival_time <= current_time:
                    available.append(p)
            
            if available:
                # En yüksek öncelikli süreci seç
                available.sort(key=lambda p: (p.priority, p.arrival_time))
                current_process = available[0]
                
                current_time = self.add_context_switch(current_time)
                
                self.add_to_gantt(current_process.process_id, current_time, current_time + current_process.burst_time)
                current_time += current_process.burst_time
                
                current_process.completion_time = current_time
                current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                current_process.is_completed = True
                completed += 1
            else:
                # IDLE
                next_arrival = processes[arrived_idx].arrival_time
                self.gantt_chart.append({
                    'process': 'IDLE',
                    'start': current_time,
                    'end': next_arrival,
                    'duration': next_arrival - current_time
                })
                current_time = next_arrival
        
        self.results = self.calculate_metrics(processes, current_time)
        return self.results


def load_processes_from_csv(filepath: str) -> List[Process]:
    """CSV dosyasından süreçleri yükler"""
    processes = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            processes.append(Process(
                process_id=row['ProcessID'],
                arrival_time=int(row['ArrivalTime']),
                burst_time=int(row['BurstTime']),
                priority=int(row['Priority'])
            ))
    return processes


class SchedulerSimulator:
    """Simülatör sınıfı - thread'li çalıştırma için"""
    
    def __init__(self, csv_file: str, quantum: int = 4):
        self.processes = load_processes_from_csv(csv_file)
        self.quantum = quantum
        self.algorithms = {
            'FCFS': None,
            'SJF_Preemptive': None,
            'SJF_Non_Preemptive': None,
            'RoundRobin': None,
            'Priority_Preemptive': None,
            'Priority_Non_Preemptive': None
        }
        self.results = {}
        self.lock = threading.Lock()
    
    def run_algorithm(self, name: str, method):
        """Algoritmayı ayrı thread'de çalıştırır"""
        scheduler = CPUScheduler(self.processes, self.quantum)
        result = method()
        with self.lock:
            self.results[name] = result
    
    def run_all_parallel(self) -> Dict[str, Any]:
        """Tüm algoritmaları paralel olarak çalıştırır (BONUS)"""
        threads = []
        
        methods = [
            ('FCFS', lambda: self.algorithms['FCFS'].fcfs()),
            ('SJF_Preemptive', lambda: self.algorithms['SJF_Preemptive'].sjf_preemptive()),
            ('SJF_Non_Preemptive', lambda: self.algorithms['SJF_Non_Preemptive'].sjf_non_preemptive()),
            ('RoundRobin', lambda: self.algorithms['RoundRobin'].round_robin()),
            ('Priority_Preemptive', lambda: self.algorithms['Priority_Preemptive'].priority_preemptive()),
            ('Priority_Non_Preemptive', lambda: self.algorithms['Priority_Non_Preemptive'].priority_non_preemptive())
        ]
        
        # Scheduler'ları oluştur
        for name, _ in methods:
            self.algorithms[name] = CPUScheduler(self.processes, self.quantum)
        
        # Thread'leri oluştur ve başlat
        for name, method in methods:
            t = threading.Thread(target=self.run_algorithm, args=(name, method))
            threads.append(t)
            t.start()
        
        # Tüm thread'lerin bitmesini bekle
        for t in threads:
            t.join()
        
        return self.results
    
    def format_gantt_chart(self, gantt_data: List[Dict]) -> str:
        """Gantt şemasını formatlı string olarak döndürür"""
        result = ""
        for entry in gantt_data:
            process = entry['process']
            start = entry['start']
            end = entry['end']
            result += f"[{start:>3}] - - {process:<8} - - [{end:>3}]\n"
        return result
    
    def generate_report(self, case_name: str) -> str:
        """Rapor üretir"""
        results = self.run_all_parallel()
        
        report = f"""
{'='*80}
{case_name} - CPU ZAMANLAMA ALGORİTMALARI RAPORU
{'='*80}

Toplam Süreç Sayısı: {len(self.processes)}
Zaman Dilimi (Quantum): {self.quantum}
Bağlam Değiştirme Süresi: {CPUScheduler.CONTEXT_SWITCH_TIME}

"""
        
        for algo_name, algo_results in results.items():
            report += f"\n{'─'*80}\n"
            report += f"ALGORİTMA: {algo_name}\n"
            report += f"{'─'*80}\n\n"
            
            # Zaman Tablosu
            report += "a) ZAMAN TABLOSU (Gantt Şeması):\n"
            report += self.format_gantt_chart(algo_results['gantt_chart'])
            report += "\n"
            
            # Bekleme Süreleri
            report += "b) BEKLEME SÜRELERİ:\n"
            report += f"   Maksimum Bekleme Süresi: {algo_results['max_waiting_time']:.3f}\n"
            report += f"   Ortalama Bekleme Süresi: {algo_results['avg_waiting_time']:.3f}\n\n"
            
            # Tamamlanma Süreleri
            report += "c) TAMAMLANMA SÜRELERİ (Turnaround Time):\n"
            report += f"   Maksimum Tamamlanma Süresi: {algo_results['max_turnaround_time']:.3f}\n"
            report += f"   Ortalama Tamamlanma Süresi: {algo_results['avg_turnaround_time']:.3f}\n\n"
            
            # Throughput
            report += "d) İŞ TAMAMLAMA SAYISI (Throughput):\n"
            for t, count in algo_results['throughput'].items():
                report += f"   T={t}: {count} süreç\n"
            report += "\n"
            
            # CPU Verimliliği
            report += "e) ORTALAMA CPU VERİMLİLİĞİ:\n"
            report += f"   CPU Kullanım Oranı: {algo_results['cpu_utilization']:.2f}%\n"
            report += f"   Toplam Bağlam Değiştirme Süresi: {algo_results['total_context_switch_time']:.3f}\n\n"
            
            # Bağlam Değiştirme Sayısı
            report += "f) TOPLAM BAĞLAM DEĞİŞTİRME SAYISI:\n"
            report += f"   {algo_results['context_switch_count']}\n"
        
        return report


if __name__ == "__main__":
    # Test
    sim1 = SchedulerSimulator("case1.csv", quantum=4)
    report1 = sim1.generate_report("CASE 1")
    print(report1)
    
    sim2 = SchedulerSimulator("case2.csv", quantum=4)
    report2 = sim2.generate_report("CASE 2")
    print(report2)
