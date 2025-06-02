// Scripts/PatientUI.cs
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class PatientUI : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    public Patient patientData;
    private CanvasGroup canvasGroup;
    private RectTransform rectTransform;
    private Transform originalParent;

    void Awake()
    {
        rectTransform = GetComponent<RectTransform>();
        canvasGroup = GetComponent<CanvasGroup>();
        originalParent = transform.parent;
    }

    public void OnBeginDrag(PointerEventData eventData)
    {
        canvasGroup.blocksRaycasts = false;
        originalParent = transform.parent;
        transform.SetParent(transform.root); // move to top layer
    }

    public void OnDrag(PointerEventData eventData)
    {
        rectTransform.anchoredPosition += eventData.delta;
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        canvasGroup.blocksRaycasts = true;
        transform.SetParent(originalParent); // fallback
        rectTransform.anchoredPosition = Vector2.zero;
    }

    public void SetPatient(Patient p)
    {
        patientData = p;
        GetComponentInChildren<Text>().text = $"{p.Name} | {p.Priority} | {p.ExamBundle.Name}";
    }
}
