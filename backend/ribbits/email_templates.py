"""
Email Templates for Croak Notifications
HTML and text versions of all email types
"""

def get_base_template(content, recipient_name="there"):
    """Base HTML template for all emails"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #10b981;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            color: #10b981;
        }}
        .content {{
            padding: 20px 0;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #10b981;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🐸 Croak</div>
        </div>
        <div class="content">
            <p>Hey {recipient_name},</p>
            {content}
        </div>
        <div class="footer">
            <p>You're receiving this because you have notifications enabled on Croak.</p>
            <p><a href="https://croak.com/settings/notifications" style="color: #10b981;">Manage your email preferences</a></p>
        </div>
    </div>
</body>
</html>
"""
    return html


def get_like_email(context):
    """Email for when someone likes your post"""
    sender = context.get('sender', 'Someone')
    post_preview = context.get('post_text', '')[:100]
    post_url = context.get('post_url', '#')
    
    subject = f"👍 {sender} liked your post"
    
    html_content = f"""
        <h2>👍 New Like!</h2>
        <p><strong>{sender}</strong> liked your post:</p>
        <blockquote style="background-color: #f9fafb; padding: 15px; border-left: 4px solid #10b981; margin: 20px 0;">
            {post_preview}...
        </blockquote>
        <a href="{post_url}" class="button">View Post</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{sender} liked your post:
"{post_preview}..."

View it here: {post_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_comment_email(context):
    """Email for when someone comments on your post"""
    sender = context.get('sender', 'Someone')
    comment_text = context.get('comment_text', '')
    post_preview = context.get('post_text', '')[:100]
    post_url = context.get('post_url', '#')
    
    subject = f"💬 {sender} commented on your post"
    
    html_content = f"""
        <h2>💬 New Comment!</h2>
        <p><strong>{sender}</strong> commented on your post:</p>
        <div style="background-color: #f9fafb; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">Your post:</p>
            <p style="margin: 5px 0;">{post_preview}...</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 10px 0;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">{sender}'s comment:</p>
            <p style="margin: 5px 0; font-weight: 500;">{comment_text}</p>
        </div>
        <a href="{post_url}" class="button">Reply</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{sender} commented on your post:

Your post: "{post_preview}..."

{sender}'s comment: "{comment_text}"

Reply here: {post_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_follow_email(context):
    """Email for when someone follows you"""
    sender = context.get('sender', 'Someone')
    sender_bio = context.get('sender_bio', '')
    profile_url = context.get('profile_url', '#')
    
    subject = f"👤 {sender} started following you"
    
    html_content = f"""
        <h2>👤 New Follower!</h2>
        <p><strong>{sender}</strong> started following you on Croak.</p>
        {f'<p style="color: #6b7280;">{sender_bio}</p>' if sender_bio else ''}
        <a href="{profile_url}" class="button">View Profile</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{sender} started following you on Croak!

{sender_bio if sender_bio else ''}

Check out their profile: {profile_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_mention_email(context):
    """Email for when someone mentions you"""
    sender = context.get('sender', 'Someone')
    post_text = context.get('post_text', '')
    post_url = context.get('post_url', '#')
    
    subject = f"📢 {sender} mentioned you"
    
    html_content = f"""
        <h2>📢 You were mentioned!</h2>
        <p><strong>{sender}</strong> mentioned you in a post:</p>
        <blockquote style="background-color: #f9fafb; padding: 15px; border-left: 4px solid #10b981; margin: 20px 0;">
            {post_text}
        </blockquote>
        <a href="{post_url}" class="button">View Post</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{sender} mentioned you in a post:

"{post_text}"

View it here: {post_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_reply_email(context):
    """Email for when someone replies to your comment"""
    sender = context.get('sender', 'Someone')
    reply_text = context.get('reply_text', '')
    your_comment = context.get('your_comment', '')
    post_url = context.get('post_url', '#')
    
    subject = f"💬 {sender} replied to your comment"
    
    html_content = f"""
        <h2>💬 New Reply!</h2>
        <p><strong>{sender}</strong> replied to your comment:</p>
        <div style="background-color: #f9fafb; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">Your comment:</p>
            <p style="margin: 5px 0;">{your_comment}</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 10px 0;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">{sender}'s reply:</p>
            <p style="margin: 5px 0; font-weight: 500;">{reply_text}</p>
        </div>
        <a href="{post_url}" class="button">View Conversation</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{sender} replied to your comment:

Your comment: "{your_comment}"

{sender}'s reply: "{reply_text}"

View the conversation: {post_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_daily_digest_email(digest_data, recipient):
    """Daily digest email with summary of activity"""
    new_followers = digest_data.get('new_followers', 0)
    total_likes = digest_data.get('total_likes', 0)
    total_comments = digest_data.get('total_comments', 0)
    trending_posts = digest_data.get('trending_posts', [])
    
    subject = f"🐸 Your Daily Croak Digest - {new_followers} new followers!"
    
    stats_html = f"""
        <div style="background-color: #f0fdf4; padding: 20px; border-radius: 6px; margin: 20px 0;">
            <h3 style="margin-top: 0;">📊 Your Stats Today</h3>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 8px 0;">👥 <strong>{new_followers}</strong> new followers</li>
                <li style="padding: 8px 0;">❤️ <strong>{total_likes}</strong> likes received</li>
                <li style="padding: 8px 0;">💬 <strong>{total_comments}</strong> comments received</li>
            </ul>
        </div>
    """
    
    trending_html = ""
    if trending_posts:
        trending_html = "<h3>🔥 Trending on Croak</h3>"
        for post in trending_posts[:3]:
            trending_html += f"""
            <div style="background-color: #f9fafb; padding: 15px; border-radius: 6px; margin: 10px 0;">
                <p style="margin: 0; font-weight: 500;">@{post.get('author', 'user')}</p>
                <p style="margin: 5px 0;">{post.get('text', '')[:150]}...</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">
                    ❤️ {post.get('likes', 0)} · 💬 {post.get('comments', 0)}
                </p>
            </div>
            """
    
    html_content = f"""
        <h2>🌅 Good morning!</h2>
        <p>Here's what happened on Croak while you were away:</p>
        {stats_html}
        {trending_html}
        <a href="https://croak.com" class="button">Open Croak</a>
    """
    
    html_body = get_base_template(html_content, recipient.first_name or recipient.username)
    
    text_body = f"""
Hey {recipient.first_name or recipient.username},

Here's your daily Croak digest:

📊 Your Stats Today:
- {new_followers} new followers
- {total_likes} likes received
- {total_comments} comments received

🔥 Trending on Croak:
{chr(10).join([f"@{p.get('author')}: {p.get('text', '')[:100]}..." for p in trending_posts[:3]])}

Open Croak: https://croak.com

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body
