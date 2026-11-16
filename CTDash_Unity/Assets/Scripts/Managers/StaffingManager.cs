// StaffingManager — controls tech availability by game-time hour.
// Drives which scanners are open (Idle) vs locked (Locked).
// Handles tech arrival and departure events.

using System.Collections.Generic;

namespace CTDash
{
    public class StaffingManager
    {
        private readonly ScannerManager              _scannerManager;
        private readonly Dictionary<string, Tech>    _allTechs    = new Dictionary<string, Tech>();
        private readonly Dictionary<string, Tech>    _activeTechs = new Dictionary<string, Tech>();

        public StaffingManager(ScannerManager scannerManager)
        {
            _scannerManager = scannerManager;

            foreach (var row in TechRoster.Roster)
            {
                _allTechs[row.Id] = new Tech(
                    techId:        row.Id,
                    name:          row.Name,
                    speed:         row.Speed,
                    accuracy:      row.Accuracy,
                    willingness:   row.Willingness,
                    knowledgeBase: row.KnowledgeBase,
                    shiftStart:    row.ShiftStart,
                    shiftEnd:      row.ShiftEnd
                );
            }
        }

        public void Tick(float gameHour)
        {
            foreach (var tech in _allTechs.Values)
            {
                bool onShift  = tech.ShiftStart <= gameHour && gameHour < tech.ShiftEnd;
                bool isActive = _activeTechs.ContainsKey(tech.TechId);

                if (onShift && !isActive)
                {
                    tech.Status = TechStatus.Idle;
                    _activeTechs[tech.TechId] = tech;
                    AssignTechToScanner(tech);
                }
                else if (!onShift && isActive)
                {
                    UnassignTech(tech);
                    tech.Status = TechStatus.OffShift;
                    _activeTechs.Remove(tech.TechId);
                }
            }
        }

        public Dictionary<string, Tech> GetActiveTechs() => _activeTechs;

        private void AssignTechToScanner(Tech tech)
        {
            foreach (var scanner in _scannerManager.Scanners.Values)
            {
                if (scanner.AssignedTech != null) continue;
                scanner.AssignedTech = tech.TechId;
                tech.AssignedScanner = scanner.ScannerId;
                if (scanner.State == ScannerState.Locked)
                    scanner.State = ScannerState.Idle;
                return;
            }
        }

        private void UnassignTech(Tech tech)
        {
            if (tech.AssignedScanner == null) return;
            if (!_scannerManager.Scanners.TryGetValue(tech.AssignedScanner, out var scanner)) return;

            scanner.AssignedTech = null;
            tech.AssignedScanner = null;
            if (scanner.State == ScannerState.Idle)
                scanner.State = ScannerState.Locked;
        }
    }
}
