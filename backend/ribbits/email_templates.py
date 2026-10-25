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
            border-bottom: 2px solid #1d9bf0;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            color: #1d9bf0;
        }}
        .content {{
            padding: 20px 0;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #1d9bf0;
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
            <p><a href="https://croak-green-shine.vercel.app/email-settings" style="color: #1d9bf0;">Manage your email preferences</a></p>
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
    from html import escape
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
                <p style="margin: 0; font-weight: 500;">@{escape(post.get('author', 'user'))}</p>
                <p style="margin: 5px 0;">{escape(post.get('text', '')[:150])}...</p>
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
        <a href="https://croak-green-shine.vercel.app/index" class="button">Open Croak</a>
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

Open Croak: https://croak-green-shine.vercel.app/index

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_new_post_from_following_email(context):
    """Email for when someone you follow creates a new post"""
    author_name = context.get('author_name', 'Someone')
    author_username = context.get('author_username', 'user')
    post_text = context.get('post_text', '')
    post_url = context.get('post_url', '#')
    has_media = context.get('has_media', False)
    
    subject = f"📝 {author_name} just posted on Croak!"
    
    media_indicator = ""
    if has_media:
        media_indicator = '<p style="color: #10b981; font-size: 14px; margin: 10px 0;">📷 Includes media</p>'
    
    html_content = f"""
        <h2>📝 New Post from @{author_username}!</h2>
        <p><strong>{author_name}</strong> just shared something new on Croak:</p>
        <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0;">
            <p style="margin: 0; font-size: 16px; line-height: 1.6;">{post_text[:300]}{'...' if len(post_text) > 300 else ''}</p>
            {media_indicator}
        </div>
        <p style="color: #6b7280;">Don't miss out on the conversation!</p>
        <a href="{post_url}" class="button">View Post</a>
    """
    
    html_body = get_base_template(html_content, context.get('recipient_name', 'there'))
    
    text_body = f"""
Hey {context.get('recipient_name', 'there')},

{author_name} (@{author_username}) just posted on Croak:

"{post_text[:200]}{'...' if len(post_text) > 200 else ''}"

View the full post: {post_url}

---
Croak - Free Voices. Real Connections.
"""
    
    return subject, html_body, text_body


def get_daily_reminder_email(recipient):
    """Daily reminder email with engaging, rotating messages"""
    import random
    
    # Collection of 20+ engaging reminder messages
    reminder_messages = [
        {
            "subject": "🐸 Your friends are croaking! Don't miss out",
            "greeting": "The Croak community is buzzing today!",
            "message": "Your feed is full of fresh ribbits, interesting conversations, and new connections waiting to be made. Jump back in and see what everyone's talking about!",
            "cta": "Check Your Feed"
        },
        {
            "subject": "✨ See what's trending on Croak today",
            "greeting": "Trending now on Croak!",
            "message": "The most interesting voices are sharing their thoughts right now. Don't let the best ribbits of the day slip by - your next favorite post might be just a scroll away.",
            "cta": "Explore Trending"
        },
        {
            "subject": "🎯 Your daily dose of Croak awaits!",
            "greeting": "Time for your daily Croak fix!",
            "message": "Fresh perspectives, lively discussions, and the voices you love are all waiting for you. Take a quick break and catch up with what matters.",
            "cta": "Dive In"
        },
        {
            "subject": "🌟 Your next favorite post might be one click away",
            "greeting": "Something amazing is waiting for you!",
            "message": "Every day on Croak brings new discoveries. That mind-blowing insight, hilarious meme, or heartfelt story you've been looking for could be in your feed right now.",
            "cta": "Discover Now"
        },
        {
            "subject": "💚 The croak you've been waiting for might be here today",
            "greeting": "Your community needs you!",
            "message": "Voices on Croak are sharing, connecting, and creating meaningful conversations. Your perspective could be the missing piece someone's looking for today.",
            "cta": "Join the Conversation"
        },
        {
            "subject": "🔥 Hot takes and cool ribbits - all in your feed",
            "greeting": "The conversation is heating up!",
            "message": "From thought-provoking discussions to lighthearted moments, your Croak feed has it all. See what's making waves in your community today.",
            "cta": "See What's Hot"
        },
        {
            "subject": "👀 You're missing some great conversations",
            "greeting": "FOMO alert!",
            "message": "While you've been away, your follows have been sharing some incredible content. Don't get left behind - jump back in and catch up on what matters!",
            "cta": "Catch Up Now"
        },
        {
            "subject": "🎉 New day, new ribbits, new vibes!",
            "greeting": "Fresh content is calling your name!",
            "message": "Today's a brand new opportunity to connect, share, and discover. Your Croak community has been active - see what surprises await you in your feed.",
            "cta": "Start Exploring"
        },
        {
            "subject": "💡 Brilliant ideas are being shared right now",
            "greeting": "Inspiration is waiting!",
            "message": "Some of the most insightful conversations are happening on Croak today. Get inspired, share your thoughts, and be part of something bigger.",
            "cta": "Get Inspired"
        },
        {
            "subject": "🚀 Your community is thriving - come see!",
            "greeting": "The Croak community grows stronger every day!",
            "message": "New members, fresh perspectives, and exciting conversations are making Croak better than ever. Be part of the energy and see what's new.",
            "cta": "Explore Community"
        },
        {
            "subject": "☕ Perfect time for a Croak break",
            "greeting": "Take a moment for yourself!",
            "message": "Whether you're grabbing coffee, taking a breather, or just need a mental reset, your Croak feed is the perfect companion. Quick scroll, big smiles.",
            "cta": "Take Your Break"
        },
        {
            "subject": "🎨 Creative minds are sharing today",
            "greeting": "Creativity is flowing on Croak!",
            "message": "Artists, thinkers, and creators are filling your feed with amazing content. From stunning visuals to brilliant ideas - come see what's being shared.",
            "cta": "View Creativity"
        },
        {
            "subject": "⚡ Quick check-in: Your feed awaits",
            "greeting": "Just a friendly reminder!",
            "message": "You don't need hours - just a few minutes can reconnect you with the voices and content you love. Your community is active and your feed is ready.",
            "cta": "Quick Check-In"
        },
        {
            "subject": "🌈 Something good is on your feed today",
            "greeting": "Good vibes incoming!",
            "message": "Whether it's a laugh, a thought-provoking idea, or a heartwarming moment - your Croak feed has something special waiting for you today.",
            "cta": "Find Your Vibe"
        },
        {
            "subject": "📣 Voices you care about are speaking",
            "greeting": "Your follows are active!",
            "message": "The people you chose to follow are sharing their thoughts, experiences, and moments. Stay connected with the voices that matter to you.",
            "cta": "Stay Connected"
        },
        {
            "subject": "🎪 The show goes on - don't miss it!",
            "greeting": "Entertainment alert!",
            "message": "From funny moments to fascinating discussions, Croak never stops being interesting. Come for the entertainment, stay for the community.",
            "cta": "Join the Show"
        },
        {
            "subject": "🌻 Start your day with fresh perspectives",
            "greeting": "Good morning, Croaker!",
            "message": "Begin your day by connecting with diverse voices and fresh ideas. Your morning scroll on Croak might just inspire your entire day!",
            "cta": "Start Your Day"
        },
        {
            "subject": "🎯 Don't let great content pass you by",
            "greeting": "Quality content alert!",
            "message": "Your feed is curated with exactly the content you love. From the people you follow to the topics you care about - it's all waiting for you.",
            "cta": "See Quality Content"
        },
        {
            "subject": "💫 Magic happens when you show up",
            "greeting": "Be present. Be connected.",
            "message": "Every time you engage on Croak, you're part of something meaningful. Your likes, comments, and shares make this community thrive. Come add your magic!",
            "cta": "Be Part of It"
        },
        {
            "subject": "🎁 Your personalized feed is a gift",
            "greeting": "Unwrap your daily dose!",
            "message": "We've carefully curated content from voices you love, topics you follow, and conversations that matter to you. Your personalized Croak experience awaits.",
            "cta": "Open Your Gift"
        },
        {
            "subject": "🌙 Evening vibes on Croak are immaculate",
            "greeting": "Wind down with Croak!",
            "message": "End your day with some chill scrolling. Catch up on what you missed, share your day's thoughts, and connect before you clock out.",
            "cta": "Evening Scroll"
        },
        {
            "subject": "🔔 Your notification bell is ringing",
            "greeting": "Activity alert!",
            "message": "People are engaging with your content, new followers found you, and conversations are happening. See what's new in your Croak world!",
            "cta": "Check Notifications"
        },
        {
            "subject": "🎵 Your feed has rhythm - come feel it",
            "greeting": "The pulse of Croak!",
            "message": "There's an energy to Croak that you can only feel when you're here. From rapid-fire threads to thoughtful exchanges - feel the rhythm of real connection.",
            "cta": "Feel the Vibe"
        },
    ]
    
    # Randomly select one message
    selected = random.choice(reminder_messages)
    
    subject = selected["subject"]
    
    html_content = f"""
        <h2>{selected["greeting"]}</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #444;">
            {selected["message"]}
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://croak-green-shine.vercel.app" class="button" style="font-size: 18px; padding: 15px 30px;">
                {selected["cta"]} 🐸
            </a>
        </div>
        <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 30px;">
            Keep croaking, keep connecting! 💚
        </p>
    """
    
    html_body = get_base_template(html_content, recipient.first_name or recipient.username)
    
    text_body = f"""
Hey {recipient.first_name or recipient.username},

{selected["greeting"]}

{selected["message"]}

{selected["cta"]}: https://croak-green-shine.vercel.app

Keep croaking, keep connecting! 💚

---
Croak - Free Voices. Real Connections.
"""

    return subject, html_body, text_body


def get_weekly_nudge_email(recipient, needs_post_reminder=False, suggested_users=None):
    """
    Weekly growth email combining whichever sections apply for this user:
    - A nudge to post if they haven't shared anything in a while
    - Suggested people to follow

    Args:
        recipient: User object
        needs_post_reminder: bool, True if the user hasn't posted recently
        suggested_users: list of dicts [{ 'username', 'first_name', 'followers_count' }, ...]
    """
    suggested_users = suggested_users or []
    name = recipient.first_name or recipient.username

    post_reminder_html = ""
    if needs_post_reminder:
        post_reminder_html = """
        <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; border-left: 4px solid #1d9bf0; margin: 20px 0;">
            <h3 style="margin-top: 0;">📸 It's been quiet on your end</h3>
            <p style="margin: 0;">
                You haven't posted on Croak in a while. Your followers would love to hear from you —
                share a thought, a photo, or whatever's on your mind.
            </p>
            <a href="https://croak-green-shine.vercel.app/index" class="button">Post Something</a>
        </div>
        """

    suggestions_html = ""
    if suggested_users:
        cards = ""
        for u in suggested_users:
            display_name = u.get("first_name") or u["username"]
            cards += f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background-color: #f9fafb; border-radius: 8px; margin: 8px 0;">
                <div>
                    <p style="margin: 0; font-weight: 600;">{display_name}</p>
                    <p style="margin: 2px 0 0; color: #6b7280; font-size: 14px;">@{u['username']} · {u.get('followers_count', 0)} followers</p>
                </div>
                <a href="https://croak-green-shine.vercel.app/user/{u['username']}" style="color: #1d9bf0; text-decoration: none; font-weight: 600; font-size: 14px;">View Profile</a>
            </div>
            """
        suggestions_html = f"""
        <div style="margin: 20px 0;">
            <h3>👋 People you might want to follow</h3>
            {cards}
        </div>
        """

    subject = "🐸 Your weekly Croak check-in"
    if needs_post_reminder and suggested_users:
        subject = "🐸 We miss your posts + some new people to follow"
    elif needs_post_reminder:
        subject = "🐸 Your followers miss hearing from you"
    elif suggested_users:
        subject = "🐸 A few people you might want to follow on Croak"

    html_content = f"""
        <h2>Here's your weekly Croak check-in</h2>
        {post_reminder_html}
        {suggestions_html}
        <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
            Keep croaking, keep connecting! 💚
        </p>
    """

    html_body = get_base_template(html_content, name)

    text_lines = [f"Hey {name},", "", "Here's your weekly Croak check-in.", ""]
    if needs_post_reminder:
        text_lines += [
            "It's been quiet on your end - you haven't posted in a while.",
            "Share something: https://croak-green-shine.vercel.app/index",
            "",
        ]
    if suggested_users:
        text_lines.append("People you might want to follow:")
        for u in suggested_users:
            text_lines.append(
                f"- @{u['username']} ({u.get('followers_count', 0)} followers): "
                f"https://croak-green-shine.vercel.app/user/{u['username']}"
            )
        text_lines.append("")
    text_lines += ["Keep croaking, keep connecting! 💚", "", "---", "Croak - Free Voices. Real Connections."]
    text_body = "\n".join(text_lines)

    return subject, html_body, text_body



SITE_URL = "https://croak-green-shine.vercel.app"

BLUE = "#1d9bf0"
INK = "#0f1419"
MUTED = "#536471"
CARD = "#f7f9fa"


def _shell(preheader, inner_html, footer_reason):
    from html import escape
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
</head>
<body style="margin:0;padding:0;background:#eef3f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef3f7;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:20px;overflow:hidden;">
<tr><td style="padding:22px 28px 0 28px;">
<span style="font-size:22px;font-weight:900;letter-spacing:-0.5px;color:{BLUE};">CROAK</span>
</td></tr>
{inner_html}
<tr><td style="padding:22px 28px 26px 28px;border-top:1px solid #eef1f3;">
<p style="margin:0;font-size:12px;line-height:18px;color:{MUTED};">{footer_reason}
<a href="{SITE_URL}/email-settings" style="color:{MUTED};text-decoration:underline;">Change email settings</a></p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _button(label, url):
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" style="margin:6px 0 0 0;">
<tr><td style="background:{BLUE};border-radius:999px;">
<a href="{url}" style="display:inline-block;padding:14px 28px;font-size:16px;font-weight:800;color:#ffffff;text-decoration:none;">{label}</a>
</td></tr></table>"""


def _post_card(author_name, username, text, footer=""):
    from html import escape
    body = escape(text).replace("\n", "<br>") if text else f'<span style="color:{MUTED};font-style:italic;">shared a photo or video</span>'
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CARD};border-radius:16px;margin:0 0 12px 0;">
<tr><td style="padding:16px 18px;">
<p style="margin:0 0 6px 0;font-size:14px;color:{INK};"><strong>{escape(author_name)}</strong> <span style="color:{MUTED};">@{escape(username)}</span></p>
<p style="margin:0;font-size:16px;line-height:24px;color:{INK};">{body}</p>
{footer}
</td></tr></table>"""


def get_new_post_broadcast_email(context):
    from html import escape
    author_name = context["author_name"]
    username = context["author_username"]
    text = context.get("post_text") or ""
    is_follower = context.get("is_follower", False)
    recipient_name = context.get("recipient_name", "there")
    profile_url = f"{SITE_URL}/user/{username}"

    snippet = " ".join(text.split())
    if len(snippet) > 45:
        snippet = snippet[:45].rstrip() + "…"

    if is_follower:
        subject = f"{author_name} just croaked: “{snippet}”" if snippet else f"{author_name} just shared something new"
        kicker = "SOMEONE YOU FOLLOW JUST POSTED"
    else:
        subject = f"Fresh on Croak: “{snippet}”" if snippet else f"{author_name} just dropped something on Croak"
        kicker = "FRESH FROM THE POND"

    media_note = ""
    if context.get("has_media"):
        media_note = f'<p style="margin:10px 0 0 0;font-size:13px;color:{MUTED};">📎 Includes a photo or video</p>'

    inner = f"""<tr><td style="padding:18px 28px 6px 28px;">
<p style="margin:0 0 6px 0;font-size:12px;font-weight:800;letter-spacing:1.5px;color:{BLUE};">{kicker}</p>
<h1 style="margin:0 0 18px 0;font-size:26px;line-height:32px;font-weight:900;color:{INK};">{escape(author_name)} has something to say 👀</h1>
{_post_card(author_name, username, text, media_note)}
</td></tr>
<tr><td style="padding:8px 28px 24px 28px;">
{_button("Jump into the conversation →", profile_url)}
</td></tr>"""

    html_body = _shell(
        f"Hey {recipient_name}, {author_name} just posted. Be the first to reply.",
        inner,
        "You're getting this because new-post emails are on.",
    )
    text_body = f"""Hey {recipient_name},

{author_name} (@{username}) just posted on Croak:

"{text or 'shared a photo or video'}"

Jump in: {profile_url}

Change email settings: {SITE_URL}/email-settings
"""
    return subject, html_body, text_body


EVENING_PROMPTS = [
    ("🌙 What was the best part of your day?", "What was the best part of your day?", "Big or tiny, it counts. Tell the pond."),
    ("😂 Okay but what made you laugh today?", "What made you laugh today?", "Memes, people, your own bad jokes. All welcome."),
    ("🏆 Tiny win check: what did you pull off today?", "What's one tiny win from today?", "Finished a task? Drank water? We celebrate everything here."),
    ("🔥 Hot take hour is open", "Drop your hottest take.", "Keep it spicy. Keep it kind."),
    ("🎧 What's been on repeat today?", "What song had you on repeat today?", "Share the track. Judge-free zone. Mostly."),
    ("🍜 Be honest: what did you eat today?", "What did you eat today?", "Gourmet or instant noodles, we want the details."),
    ("📸 Show us one thing from today", "Show us one photo from today.", "No filters needed. Okay, maybe one."),
    ("💭 Got a shower thought for us?", "Got a shower thought?", "The weirder, the better."),
    ("✨ What are you looking forward to?", "What's one thing you're looking forward to?", "Tomorrow, this week, someday. Say it out loud."),
    ("☕ Real talk: how was today, really?", "How was today, really?", "Good, bad, chaotic. The pond is listening."),
    ("📚 Learned anything cool today?", "What's one thing you learned today?", "Fun facts and life lessons both qualify."),
    ("🙌 Who made your day better?", "Who made your day a little better?", "Shout them out. They'll love it."),
]


def get_evening_prompt(day):
    return EVENING_PROMPTS[day.toordinal() % len(EVENING_PROMPTS)]


def get_evening_checkin_email(recipient, data, day):
    from html import escape
    subject, headline, nudge = get_evening_prompt(day)
    name = recipient.first_name or recipient.username
    post_count = data.get("post_count", 0)
    top_posts = data.get("top_posts", [])
    compose_url = f"{SITE_URL}/index"

    if post_count:
        croaks = "croak" if post_count == 1 else "croaks"
        intro = f"The pond heard <strong>{post_count} {croaks}</strong> today. Here's what people loved:"
        preheader = f"{post_count} {croaks} today. Here's what you missed, plus tonight's question."
    else:
        intro = "It's quiet in the pond tonight. Perfect timing to be the first voice of the evening."
        preheader = "It's quiet tonight. Be the first croak of the evening."

    cards = ""
    for post in top_posts[:3]:
        stats = f'<p style="margin:10px 0 0 0;font-size:13px;color:{MUTED};">❤️ {post["likes"]} &nbsp;·&nbsp; 💬 {post["comments"]}</p>'
        text = post["text"]
        if len(text) > 180:
            text = text[:180].rstrip() + "…"
        cards += _post_card(post["author_name"], post["author_username"], text, stats)

    inner = f"""<tr><td style="padding:18px 28px 0 28px;">
<p style="margin:0 0 14px 0;font-size:12px;font-weight:800;letter-spacing:1.5px;color:{BLUE};">YOUR 8 PM CHECK-IN</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BLUE};border-radius:18px;">
<tr><td style="padding:26px 24px;">
<p style="margin:0 0 8px 0;font-size:15px;color:#d6ecfd;">Hey {escape(name)}, tonight's question:</p>
<h1 style="margin:0 0 10px 0;font-size:30px;line-height:36px;font-weight:900;color:#ffffff;">{escape(headline)}</h1>
<p style="margin:0;font-size:15px;line-height:22px;color:#e8f4fe;">{escape(nudge)}</p>
</td></tr></table>
</td></tr>
<tr><td style="padding:22px 28px 4px 28px;">
<p style="margin:0 0 14px 0;font-size:15px;line-height:22px;color:{INK};">{intro}</p>
{cards}
</td></tr>
<tr><td style="padding:10px 28px 26px 28px;">
{_button("Croak about your day →", compose_url)}
</td></tr>"""

    html_body = _shell(preheader, inner, "You get this at 8 PM because evening check-ins are on.")

    top_text = "\n".join(f"- @{p['author_username']}: {p['text'][:120]}" for p in top_posts[:3])
    text_body = f"""Hey {name}, tonight's question:

{headline}
{nudge}

{f"{post_count} croaks today. Top ones:" if post_count else "It's quiet tonight. Be the first croak of the evening."}
{top_text}

Croak about your day: {compose_url}

Change email settings: {SITE_URL}/email-settings
"""
    return subject, html_body, text_body
