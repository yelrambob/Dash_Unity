// PatientCard — displays one patient's key info.
// Instantiate from a prefab and call Bind() to attach to a Patient.
// The queue list / holding bay list UI will instantiate these.

using UnityEngine;
using UnityEngine.UI;

namespace CTDash
{
    public class PatientCard : MonoBehaviour
    {
        [Header("UI Elements")]
        public Text IdText;
        public Text AcuityText;
        public Text StateText;
        public Text ExamText;
        public Text WaitText;
        public Image AcuityBadge;

        [Header("Acuity Badge Colours")]
        public Color Acuity1Colour = new Color(0.8f, 0.0f, 0.0f);   // deep red
        public Color Acuity2Colour = new Color(0.9f, 0.4f, 0.0f);   // orange
        public Color Acuity3Colour = new Color(0.9f, 0.8f, 0.0f);   // yellow
        public Color Acuity4Colour = new Color(0.2f, 0.6f, 0.2f);   // green

        private Patient _patient;

        public void Bind(Patient patient) => _patient = patient;

        private void Update()
        {
            if (_patient == null) return;

            if (IdText)     IdText.text     = _patient.PatientId;
            if (AcuityText) AcuityText.text = $"T{_patient.Acuity}";
            if (StateText)  StateText.text  = _patient.State.ToString();
            if (ExamText && _patient.CurrentExamIndex < _patient.ExamList.Count)
                ExamText.text = _patient.ExamList[_patient.CurrentExamIndex];
            if (WaitText)   WaitText.text   = $"{_patient.WaitTimer / 60}m {_patient.WaitTimer % 60}s";

            if (AcuityBadge)
                AcuityBadge.color = _patient.Acuity switch
                {
                    1 => Acuity1Colour,
                    2 => Acuity2Colour,
                    3 => Acuity3Colour,
                    _ => Acuity4Colour,
                };
        }
    }
}
