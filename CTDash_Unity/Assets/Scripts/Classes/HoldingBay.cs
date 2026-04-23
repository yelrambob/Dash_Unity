// HoldingBay — waiting area before scanner assignment.
// Tracks proper slots and overflow slots separately.
// Overflow triggers a penalty via ScoringManager.

using System.Collections.Generic;

namespace CTDash
{
    public class HoldingBay
    {
        public string       Zone;
        public int          ProperSlots;
        public int          OverflowSlots;
        public List<string> Patients = new List<string>();   // PatientIds

        public bool IsOverflowing => Patients.Count > ProperSlots;
        public bool IsFull        => Patients.Count >= (ProperSlots + OverflowSlots);

        public HoldingBay(string zone, int properSlots = 4, int overflowSlots = 3)
        {
            Zone          = zone;
            ProperSlots   = properSlots;
            OverflowSlots = overflowSlots;
        }
    }
}
