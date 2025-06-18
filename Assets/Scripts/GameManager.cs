// Scripts/GameManager.cs
using System.Collections.Generic;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    public List<CTScanner> Scanners;
    private List<Patient> waitingQueue = new List<Patient>();

    void Start()
    {
        // TEMP TEST: Spawn one patient
        ExamBundle headCT = new ExamBundle("Head CT", 5f);
        Patient testPatient = new Patient("John Doe", "STAT", headCT);
        waitingQueue.Add(testPatient);
    }

    void Update()
    {
        AutoAssignPatients();
    }

    void AutoAssignPatients()
    {
        foreach (CTScanner scanner in Scanners)
        {
            if (scanner.Status == CTScanner.ScannerStatus.Idle && waitingQueue.Count > 0)
            {
                Patient next = waitingQueue[0];
                waitingQueue.RemoveAt(0);
                scanner.StartScan(next);
            }
        }
    }
}
