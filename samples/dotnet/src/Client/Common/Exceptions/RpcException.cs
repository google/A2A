namespace Client.Common.Exceptions;

/// <summary>
/// Exception for RPC errors in the A2A protocol.
/// </summary>
public class RpcException : Exception
{
    /// <summary>
    /// The error code.
    /// </summary>
    public int Code { get; }

    /// <summary>
    /// Additional error data.
    /// </summary>
    public new object Data { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RpcException"/> class.
    /// </summary>
    /// <param name="code">The error code.</param>
    /// <param name="message">The error message.</param>
    /// <param name="data">Additional error data.</param>
    public RpcException(int code, string message, object data = null!)
        : base(message)
    {
        Code = code;
        Data = data;
    }
}