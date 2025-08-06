using UnityEngine;
using System.Collections;

public class BotController : MonoBehaviour
{
    Difficulty difficulty = Difficulty.Normal;
    bool started;

    public void SetDifficulty(Difficulty d) => difficulty = d;

    void Start()
    {
        if (!started) StartCoroutine(BotLoop());
    }

    IEnumerator BotLoop()
    {
        started = true;
        while (true)
        {
            // Simulate "thinking time" by difficulty
            float think = difficulty switch
            {
                Difficulty.Easy => 0.5f,
                Difficulty.Normal => 1.0f,
                Difficulty.Hard => 1.5f,
                _ => 1.0f
            };
            yield return new WaitForSeconds(think);

            // TODO: replace this with real board AI move selection
            // For now, random jitter so you can see it's alive
            transform.position += new Vector3(Random.Range(-0.2f, 0.2f), 0, Random.Range(-0.2f, 0.2f));
        }
    }
}

