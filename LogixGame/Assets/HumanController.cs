using UnityEngine;

public class HumanController : MonoBehaviour
{
    // Replace with your board input later
    void Update()
    {
        // Example placeholder: WASD nudge
        float x = Input.GetAxis("Horizontal");
        float y = Input.GetAxis("Vertical");
        transform.position += new Vector3(x, 0, y) * Time.deltaTime * 2f;
    }
}

