// Scripts/HoldingBay.cs
using System.Collections.Generic;
using UnityEngine;

public class HoldingBay : MonoBehaviour
{
    public Transform slotContainer;
    public GameObject patientUIPrefab;
    public int maxSlots = 4;

    private List<Patient> currentPatients = new List<Patient>();

    public void AddPatient(Patient patient)
    {
        if (currentPatients.Count >= maxSlots) return;

        currentPatients.Add(patient);
        GameObject ui = Instantiate(patientUIPrefab, slotContainer);
        ui.GetComponent<PatientUI>().SetPatient(patient);
    }

    public void ClearBay()
    {
        currentPatients.Clear();
        foreach (Transform child in slotContainer)
        {
            Destroy(child.gameObject);
        }
    }
}
