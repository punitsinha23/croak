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

