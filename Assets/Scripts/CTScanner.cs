// Scripts/CTScanner.cs
using UnityEngine;

public class CTScanner : MonoBehaviour
{
    public enum ScannerStatus { Idle, Scanning, Cooldown }

    public ScannerStatus Status = ScannerStatus.Idle;
    public Patient CurrentPatient;

    public float ScanTimer = 0f;
    public float CooldownTimer = 0f;
    public float CooldownDuration = 5f;

    void Update()
    {
        switch (Status)
        {
            case ScannerStatus.Scanning:
                ScanTimer -= Time.deltaTime;
                if (ScanTimer <= 0f)
                {
                    Status = ScannerStatus.Cooldown;
                    CooldownTimer = CooldownDuration;
                    Debug.Log($"Scanner {name} finished scanning {CurrentPatient.Name}");
                }
                break;

            case ScannerStatus.Cooldown:
                CooldownTimer -= Time.deltaTime;
                if (CooldownTimer <= 0f)
                {
                    Status = ScannerStatus.Idle;
                    CurrentPatient = null;
                    Debug.Log($"Scanner {name} is idle again");
                }
                break;
        }
    }

    public void StartScan(Patient patient)
    {
        CurrentPatient = patient;
        ScanTimer = patient.ExamBundle.ScanTime;
        Status = ScannerStatus.Scanning;
        Debug.Log($"Scanner {name} started scanning {patient.Name}");
    }
}
