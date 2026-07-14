using System;
using Unity.InferenceEngine;
using UnityEngine;

public class LogixNeuralNetwork : MonoBehaviour
{
    [Header("Model")]
    [SerializeField]
    private ModelAsset modelAsset;

    [Header("Tensor names")]
    [SerializeField]
    private string boardInputName = "board";

    [SerializeField]
    private string featureInputName = "features";

    [SerializeField]
    private string policyOutputName = "policy";

    [SerializeField]
    private string valueOutputName = "value";

    [Header("Backend")]
    [SerializeField]
    private BackendType backendType = BackendType.GPUCompute;

    public const int BoardSize = 7;
    public const int BoardChannels = 6;
    public const int ActionCount = 2891;

    private Model runtimeModel;
    private Worker worker;
    private bool initialized;

    public bool IsInitialized => initialized;

    private void Awake()
    {
        Initialize();
    }

    public void Initialize()
    {
        if (initialized)
        {
            return;
        }

        if (modelAsset == null)
        {
            Debug.LogError(
                "[LogixNeuralNetwork] No ONNX model has been assigned."
            );

            return;
        }

        try
        {
            runtimeModel = ModelLoader.Load(modelAsset);
            worker = new Worker(runtimeModel, backendType);

            initialized = true;

            Debug.Log(
                $"[LogixNeuralNetwork] Model initialized using {backendType}."
            );
        }
        catch (Exception exception)
        {
            Debug.LogError(
                "[LogixNeuralNetwork] Failed to initialize model:\n" +
                exception
            );

            initialized = false;
        }
    }

    public NeuralNetworkResult Evaluate(
        float[] boardInput,
        float[] featureInput)
    {
        if (!initialized || worker == null)
        {
            throw new InvalidOperationException(
                "The neural network has not been initialized."
            );
        }

        ValidateInputs(boardInput, featureInput);

        TensorShape boardShape = new TensorShape(
            1,
            BoardChannels,
            BoardSize,
            BoardSize
        );

        TensorShape featureShape = new TensorShape(
            1,
            featureInput.Length
        );

        using Tensor<float> boardTensor = new Tensor<float>(
            boardShape,
            boardInput
        );

        using Tensor<float> featureTensor = new Tensor<float>(
            featureShape,
            featureInput
        );

        worker.SetInput(boardInputName, boardTensor);
        worker.SetInput(featureInputName, featureTensor);

        worker.Schedule();

        Tensor<float> policyTensor =
            worker.PeekOutput(policyOutputName) as Tensor<float>;

        Tensor<float> valueTensor =
            worker.PeekOutput(valueOutputName) as Tensor<float>;

        if (policyTensor == null)
        {
            throw new InvalidOperationException(
                $"Could not find policy output '{policyOutputName}'."
            );
        }

        if (valueTensor == null)
        {
            throw new InvalidOperationException(
                $"Could not find value output '{valueOutputName}'."
            );
        }

        float[] policy = policyTensor.DownloadToArray();
        float[] valueArray = valueTensor.DownloadToArray();

        if (policy.Length != ActionCount)
        {
            throw new InvalidOperationException(
                $"Expected {ActionCount} policy outputs, " +
                $"but the model returned {policy.Length}."
            );
        }

        if (valueArray.Length == 0)
        {
            throw new InvalidOperationException(
                "The value output tensor was empty."
            );
        }

        float value = Mathf.Clamp(valueArray[0], -1f, 1f);

        return new NeuralNetworkResult(policy, value);
    }

    private static void ValidateInputs(
        float[] boardInput,
        float[] featureInput)
    {
        int expectedBoardValues =
            BoardChannels * BoardSize * BoardSize;

        if (boardInput == null)
        {
            throw new ArgumentNullException(nameof(boardInput));
        }

        if (boardInput.Length != expectedBoardValues)
        {
            throw new ArgumentException(
                $"Board input must contain {expectedBoardValues} values, " +
                $"but received {boardInput.Length}.",
                nameof(boardInput)
            );
        }

        if (featureInput == null)
        {
            throw new ArgumentNullException(nameof(featureInput));
        }

        if (featureInput.Length == 0)
        {
            throw new ArgumentException(
                "Feature input cannot be empty.",
                nameof(featureInput)
            );
        }
    }

    private void OnDestroy()
    {
        worker?.Dispose();
        worker = null;
        runtimeModel = null;
        initialized = false;
    }
}

public readonly struct NeuralNetworkResult
{
    public float[] PolicyLogits { get; }
    public float Value { get; }

    public NeuralNetworkResult(
        float[] policyLogits,
        float value)
    {
        PolicyLogits = policyLogits;
        Value = value;
    }
}