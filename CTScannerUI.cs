// Scripts/CTScannerUI.cs
using UnityEngine;
using UnityEngine.UI;

public class CTScannerUI : MonoBehaviour
{
    public Image scannerImage;
    public Sprite idleSprite;
    public Animator scanningAnimator; // set this if using an Animator
    public GameObject scanningObject; // animated scanner
    public GameObject idleObject;     // static image

    public void SetState(string state)
    {
        switch (state)
        {
            case "idle":
                idleObject.SetActive(true);
                scanningObject.SetActive(false);
                break;

            case "scanning":
                idleObject.SetActive(false);
                scanningObject.SetActive(true);
                break;

            case "cooldown":
                idleObject.SetActive(true);
                scanningObject.SetActive(false);
                // Optionally add glow or timer
                break;
        }
    }
}
