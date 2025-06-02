"""
Utility functions for sending notifications.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def send_discord_webhook(webhook_url: str, content: str, embeds: Optional[List[Dict[str, Any]]] = None) -> bool:
    """
    Send a message to a Discord webhook.
    
    Args:
        webhook_url: The Discord webhook URL
        content: The main content of the message
        embeds: Optional list of embeds
        
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    if not webhook_url:
        logger.warning("No Discord webhook URL provided. Skipping notification.")
        return False
    
    payload = {"content": content}
    
    if embeds:
        payload["embeds"] = embeds
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Discord notification sent successfully: {response.status_code}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {str(e)}")
        return False


def format_discord_embeds_for_assignments(assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format assignment data as Discord embeds.
    
    Args:
        assignments: List of assignment data
        
    Returns:
        List of Discord embeds
    """
    embeds = []
    
    for assignment in assignments:
        color = 0xFF0000  # Red for urgent
        if assignment["days_remaining"] > 1:
            color = 0xFFFF00  # Yellow for warning
        if assignment["status"].lower() == "submitted":
            color = 0x00FF00  # Green for submitted
            
        embed = {
            "title": assignment["title"],
            "description": f"**Course:** {assignment['course']}\n**Deadline:** {assignment['deadline']}\n**Days Remaining:** {assignment['days_remaining']}\n**Status:** {assignment['status']}",
            "color": color,
            "url": assignment["url"]
        }
        
        embeds.append(embed)
    
    return embeds


def format_discord_embeds_for_quizzes(quizzes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format quiz data as Discord embeds.
    
    Args:
        quizzes: List of quiz data
        
    Returns:
        List of Discord embeds
    """
    embeds = []
    
    for quiz in quizzes:
        color = 0xFF0000  # Red for urgent
        if quiz["days_remaining"] > 1:
            color = 0xFFFF00  # Yellow for warning
        if quiz["status"].lower() == "completed":
            color = 0x00FF00  # Green for completed
            
        embed = {
            "title": quiz["title"],
            "description": f"**Course:** {quiz['course']}\n**Deadline:** {quiz['deadline']}\n**Days Remaining:** {quiz['days_remaining']}\n**Status:** {quiz['status']}",
            "color": color,
            "url": quiz["url"]
        }
        
        embeds.append(embed)
    
    return embeds
