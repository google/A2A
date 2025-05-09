using Microsoft.AspNetCore.Mvc;
using Server.Services;

namespace Server.Controllers;

/// <summary>
/// Controller for serving the agent card.
/// </summary>
[ApiController]
[Route("agent-card")]
public class AgentCardController : ControllerBase
{
    private readonly A2ACardService _cardService;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentCardController"/> class.
    /// </summary>
    /// <param name="cardService">The card service.</param>
    public AgentCardController(A2ACardService cardService)
    {
        _cardService = cardService;
    }

    /// <summary>
    /// Gets the agent card.
    /// </summary>
    /// <returns>The agent card.</returns>
    [HttpGet]
    public IActionResult GetAgentCard()
    {
        return Ok(_cardService.GetAgentCard());
    }
}

