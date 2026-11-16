// QueueManager — manages the ordered queue of waiting patients.
// Priority: lower acuity number = higher priority.
// Tie-broken by arrival time (earlier = higher priority).

using System.Collections.Generic;

namespace CTDash
{
    public class QueueManager
    {
        // Entry in the priority queue.
        private struct QueueEntry
        {
            public int    Acuity;
            public int    ArrivalSecond;
            public string PatientId;
        }

        private readonly List<QueueEntry>          _heap     = new List<QueueEntry>();
        public  readonly Dictionary<string, Patient> Patients = new Dictionary<string, Patient>();

        public void AddPatient(Patient patient, int gameSecond)
        {
            Patients[patient.PatientId] = patient;
            HeapPush(new QueueEntry
            {
                Acuity        = patient.Acuity,
                ArrivalSecond = gameSecond,
                PatientId     = patient.PatientId,
            });
        }

        public void Tick()
        {
            foreach (var patient in Patients.Values)
                patient.WaitTimer += GameConfig.TICK_SECONDS;
        }

        public Patient PopNext()
        {
            if (_heap.Count == 0) return null;
            var entry = HeapPop();
            if (!Patients.TryGetValue(entry.PatientId, out var patient)) return null;
            Patients.Remove(entry.PatientId);
            return patient;
        }

        public bool IsEmpty => _heap.Count == 0;

        // --- Min-heap helpers (keyed by Acuity then ArrivalSecond) ------

        private void HeapPush(QueueEntry entry)
        {
            _heap.Add(entry);
            SiftUp(_heap.Count - 1);
        }

        private QueueEntry HeapPop()
        {
            var top = _heap[0];
            int last = _heap.Count - 1;
            _heap[0] = _heap[last];
            _heap.RemoveAt(last);
            if (_heap.Count > 0) SiftDown(0);
            return top;
        }

        private void SiftUp(int i)
        {
            while (i > 0)
            {
                int parent = (i - 1) / 2;
                if (Compare(_heap[i], _heap[parent]) < 0)
                {
                    Swap(i, parent);
                    i = parent;
                }
                else break;
            }
        }

        private void SiftDown(int i)
        {
            int n = _heap.Count;
            while (true)
            {
                int smallest = i;
                int l = 2 * i + 1, r = 2 * i + 2;
                if (l < n && Compare(_heap[l], _heap[smallest]) < 0) smallest = l;
                if (r < n && Compare(_heap[r], _heap[smallest]) < 0) smallest = r;
                if (smallest == i) break;
                Swap(i, smallest);
                i = smallest;
            }
        }

        private static int Compare(QueueEntry a, QueueEntry b)
        {
            if (a.Acuity != b.Acuity) return a.Acuity.CompareTo(b.Acuity);
            return a.ArrivalSecond.CompareTo(b.ArrivalSecond);
        }

        private void Swap(int i, int j)
        {
            var tmp = _heap[i]; _heap[i] = _heap[j]; _heap[j] = tmp;
        }
    }
}
