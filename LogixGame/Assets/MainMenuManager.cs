using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenuManager : MonoBehaviour
{
    public GameObject modeSelectionPanel;
    public GameObject difficultyPanel;
    public GameObject botVsBotPanel;

    private string selectedMode = "";
    private string botADifficulty = "";
    private string botBDifficulty = "";

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {

    }

    // Update is called once per frame
    void Update()
    {

    }

    // First three buttons in Main Menu screen
    public void OnPlayClicked()
    {
        modeSelectionPanel.SetActive(true);
    }

    public void OnRulesClicked()
    {
        Debug.Log("Show rules panel or rules scene");
    }

    public void OnAboutClicked()
    {
        Debug.Log("Show about panel or rules scene");
    }

    // Three mode selection buttons
    public void OnPvPClicked()
    {
        PlayerPrefs.SetString("GameMode", "PvP");
        SceneManager.LoadScene("GameScene");
    }

    public void OnPvEClicked()
    {
        selectedMode = "PvE";
        modeSelectionPanel.SetActive(false);
        difficultyPanel.SetActive(true);
    }

    public void OnEvEClicked()
    {
        selectedMode = "EvE";
        modeSelectionPanel.SetActive(false);
        botVsBotPanel.SetActive(true);
    }

    // Difficulty selection buttons
    public void OnDifficultySelected(string difficulty)
    {
        if (selectedMode == "PvE")
        {
            PlayerPrefs.SetString("GameMode", "PvE");
            PlayerPrefs.SetString("AIDifficulty", difficulty);
            SceneManager.LoadScene("GameScene");
        }
    }
    // For Bot versus Bot selection
    public void SetBotADifficulty(string difficulty)
    {
        botADifficulty = difficulty;
    }

    public void SetBotBDifficulty(string difficulty)
    {
        botBDifficulty = difficulty;
    }

    public void OnStartEvE()
    {
        if (!string.IsNullOrEmpty(botADifficulty) && !string.IsNullOrEmpty(botBDifficulty))
        {
            PlayerPrefs.SetString("GameMode", "EvE");
            PlayerPrefs.SetString("BotA", botADifficulty);
            PlayerPrefs.SetString("BotB", botBDifficulty);
            SceneManager.LoadScene("GameScene");
        }
        else
        {
            Debug.LogWarning("Please select difficulty for both bots before starting.");
        }
    }
    // Wrapper methods for buttons that can't pass strings
    public void OnBotAEasy() => SetBotADifficulty("Easy");
    public void OnBotANormal() => SetBotADifficulty("Normal");
    public void OnBotAHard() => SetBotADifficulty("Hard");

    public void OnBotBEasy() => SetBotBDifficulty("Easy");
    public void OnBotBNormal() => SetBotBDifficulty("Normal");
    public void OnBotBHard() => SetBotBDifficulty("Hard");
}