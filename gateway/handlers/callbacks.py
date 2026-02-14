from aiogram import types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from gateway.database import channels_collection, channel_registry
from gateway.utils.captcha import generate_short_code

async def handle_stats(callback: types.CallbackQuery):
    short_code = callback.data.split("_")[1]
    channel = await channels_collection.find_one({"short_code": short_code, "owner_id": callback.from_user.id})
    
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    stats = channel.get("stats", {"total_attempts": 0, "successful_joins": 0, "failed_captcha": 0})
    auto_status = "Enabled" if channel.get("auto_accept", False) else "Disabled"
    
    text = (
        f"📊 Statistics for {channel['channel_name']}\n\n"
        f"🔗 Short Code: {short_code}\n"
        f"👥 Total Attempts: {stats['total_attempts']}\n"
        f"✅ Successful Joins: {stats['successful_joins']}\n"
        f"❌ Failed Captcha: {stats['failed_captcha']}\n"
        f"📈 Success Rate: {(stats['successful_joins'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0:.1f}%\n"
        f"🤖 Auto-Accept: {auto_status}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="« Back", callback_data="back_to_channels")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

async def handle_delete(callback: types.CallbackQuery):
    short_code = callback.data.split("_")[1]
    channel = await channels_collection.find_one({"short_code": short_code, "owner_id": callback.from_user.id})
    
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, Delete", callback_data=f"confirm_delete_{short_code}")
    builder.button(text="❌ Cancel", callback_data="back_to_channels")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"⚠️ Are you sure you want to delete?\n\n{channel['channel_name']}\n\nThis action cannot be undone!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_confirm_delete(callback: types.CallbackQuery):
    short_code = callback.data.split("_")[2]
    result = await channels_collection.delete_one({"short_code": short_code, "owner_id": callback.from_user.id})
    
    if result.deleted_count > 0:
        await callback.message.edit_text("✅ Channel deleted successfully!")
        await callback.answer("Deleted!")
    else:
        await callback.answer("Failed to delete!", show_alert=True)

async def handle_toggle_auto(callback: types.CallbackQuery):
    short_code = callback.data.split("_")[2]
    channel = await channels_collection.find_one({"short_code": short_code, "owner_id": callback.from_user.id})
    
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    new_status = not channel.get("auto_accept", False)
    await channels_collection.update_one(
        {"short_code": short_code, "owner_id": callback.from_user.id},
        {"$set": {"auto_accept": new_status}}
    )
    
    status_text = "enabled" if new_status else "disabled"
    await callback.answer(f"Auto-Accept {status_text}!", show_alert=True)
    
    # Refresh the channel list
    await handle_back(callback)

async def handle_manage_links(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    
    # Get all links for this channel
    links = await channels_collection.find({"channel_id": channel_id, "owner_id": callback.from_user.id}).to_list(length=100)
    
    if not links:
        # No links but channel exists - show option to generate first link
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Generate New Link", callback_data=f"newlink_{channel_id}")
        builder.button(text="« Back", callback_data="back_to_channels")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🔗 No active links for this channel\n\n"
            f"Generate a new link to start sharing!",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    channel_name = links[0]["channel_name"]
    bot_info = await callback.bot.get_me()
    
    text = f"🔗 Deep Links for {channel_name}\n\n"
    builder = InlineKeyboardBuilder()
    
    for link in links:
        deep_link = f"https://t.me/{bot_info.username}?start={link['short_code']}"
        stats = link.get("stats", {"total_attempts": 0})
        text += f"• {link['short_code']} - {stats['total_attempts']} attempts\n"
        builder.button(text=f"🔗 {link['short_code']}", url=deep_link)
        builder.button(text=f"🗑 Revoke", callback_data=f"revoke_{link['short_code']}")
    
    builder.button(text="➕ Generate New Link", callback_data=f"newlink_{channel_id}")
    builder.button(text="« Back", callback_data="back_to_channels")
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

async def handle_revoke_link(callback: types.CallbackQuery):
    short_code = callback.data.split("_")[1]
    
    # Get the link to revoke
    link_to_revoke = await channels_collection.find_one({"short_code": short_code, "owner_id": callback.from_user.id})
    if not link_to_revoke:
        await callback.answer("Link not found!", show_alert=True)
        return
    
    channel_id = link_to_revoke["channel_id"]
    
    # Delete the link
    result = await channels_collection.delete_one({"short_code": short_code, "owner_id": callback.from_user.id})
    
    if result.deleted_count > 0:
        await callback.answer("Link revoked!", show_alert=True)
        # Refresh the manage links view by calling it directly with channel_id
        await refresh_manage_links(callback, channel_id)
    else:
        await callback.answer("Failed to revoke!", show_alert=True)

async def refresh_manage_links(callback: types.CallbackQuery, channel_id: int):
    # Get all links for this channel
    links = await channels_collection.find({"channel_id": channel_id, "owner_id": callback.from_user.id}).to_list(length=100)
    
    if not links:
        # No links but channel exists - show option to generate first link
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Generate New Link", callback_data=f"newlink_{channel_id}")
        builder.button(text="« Back", callback_data="back_to_channels")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🔗 No active links for this channel\n\n"
            f"Generate a new link to start sharing!",
            reply_markup=builder.as_markup()
        )
        return
    
    channel_name = links[0]["channel_name"]
    bot_info = await callback.bot.get_me()
    
    text = f"🔗 Deep Links for {channel_name}\n\n"
    builder = InlineKeyboardBuilder()
    
    for link in links:
        deep_link = f"https://t.me/{bot_info.username}?start={link['short_code']}"
        stats = link.get("stats", {"total_attempts": 0})
        text += f"• {link['short_code']} - {stats['total_attempts']} attempts\n"
        builder.button(text=f"🔗 {link['short_code']}", url=deep_link)
        builder.button(text=f"🗑 Revoke", callback_data=f"revoke_{link['short_code']}")
    
    builder.button(text="➕ Generate New Link", callback_data=f"newlink_{channel_id}")
    builder.button(text="« Back", callback_data="back_to_channels")
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

async def handle_new_link(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    
    # Get channel info from registry
    existing = await channel_registry.find_one({"channel_id": channel_id, "owner_id": callback.from_user.id})
    if not existing:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    # Generate new link
    from datetime import datetime
    short_code = generate_short_code()
    await channels_collection.insert_one({
        "short_code": short_code,
        "channel_id": channel_id,
        "channel_name": existing["channel_name"],
        "owner_id": callback.from_user.id,
        "created_at": datetime.utcnow(),
        "stats": {"total_attempts": 0, "successful_joins": 0, "failed_captcha": 0},
        "auto_accept": existing.get("auto_accept", False)
    })
    
    bot_info = await callback.bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start={short_code}"
    
    await callback.answer(f"New link generated: {short_code}", show_alert=True)
    # Refresh the links view
    await refresh_manage_links(callback, channel_id)

async def handle_help(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="« Back", callback_data="back_to_start")
    
    await callback.message.edit_text(
        "📚 How to Use Gateway Bot\n\n"
        "📌 Add Your Channel (3 Ways):\n"
        "1️⃣ /addchannel <channel_id>\n"
        "2️⃣ Make bot admin in your channel (auto-adds)\n"
        "3️⃣ Forward any message from your channel\n\n"
        "📊 Manage Channels:\n"
        "/mychannels - View all your channels\n\n"
        "🔗 Features:\n"
        "• Generate unlimited deep links\n"
        "• Revoke/create new links anytime\n"
        "• Track statistics per link\n"
        "• Auto-accept join requests\n"
        "• Captcha verification for security",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_my_channels_btn(callback: types.CallbackQuery):
    await handle_back(callback)

async def handle_back_to_start(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Help", callback_data="help")
    builder.button(text="📊 My Channels", callback_data="my_channels_btn")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "👋 Welcome to Gateway Bot!\n\n"
        "🔒 Secure your private channels with captcha verification\n"
        "🔗 Generate unlimited deep links\n"
        "📊 Track statistics for each link\n\n"
        "Click Help to get started!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Get all registered channels
    registered_channels = await channel_registry.find({"owner_id": user_id}).to_list(length=100)
    
    if not registered_channels:
        await callback.message.edit_text("You haven't added any channels yet.\nUse /addchannel <channel_id> to add one.")
        await callback.answer()
        return
    
    builder = InlineKeyboardBuilder()
    
    for reg_channel in registered_channels:
        channel_id = reg_channel["channel_id"]
        channel_name = reg_channel["channel_name"]
        
        # Count links for this channel
        link_count = await channels_collection.count_documents({"channel_id": channel_id, "owner_id": user_id})
        
        builder.button(text=f"{channel_name} ({link_count})", callback_data=f"viewchannel_{channel_id}")
    
    builder.adjust(1)
    
    await callback.message.edit_text("📋 Your Channels:", reply_markup=builder.as_markup())
    await callback.answer()

async def handle_view_channel(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Get channel from registry
    channel = await channel_registry.find_one({"channel_id": channel_id, "owner_id": user_id})
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    # Count links
    link_count = await channels_collection.count_documents({"channel_id": channel_id, "owner_id": user_id})
    auto_status = "✅ Enabled" if channel.get("auto_accept", False) else "❌ Disabled"
    
    text = (
        f"📊 {channel['channel_name']}\n\n"
        f"🔗 Active Links: {link_count}\n"
        f"🤖 Auto-Accept: {auto_status}\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Manage Links", callback_data=f"managelinks_{channel_id}")
    builder.button(text="🤖 Toggle Auto-Accept", callback_data=f"toggle_auto_channel_{channel_id}")
    builder.button(text="🗑 Delete Channel", callback_data=f"deletechannel_{channel_id}")
    builder.button(text="« Back", callback_data="back_to_channels")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

async def handle_toggle_auto_channel(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    # Get current status from registry
    channel = await channel_registry.find_one({"channel_id": channel_id, "owner_id": user_id})
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    new_status = not channel.get("auto_accept", False)
    
    # Update in registry
    await channel_registry.update_one(
        {"channel_id": channel_id, "owner_id": user_id},
        {"$set": {"auto_accept": new_status}}
    )
    
    # Update all links for this channel
    await channels_collection.update_many(
        {"channel_id": channel_id, "owner_id": user_id},
        {"$set": {"auto_accept": new_status}}
    )
    
    status_text = "enabled" if new_status else "disabled"
    await callback.answer(f"Auto-Accept {status_text}!", show_alert=True)
    
    # Refresh view
    callback.data = f"viewchannel_{channel_id}"
    await handle_view_channel(callback)

async def handle_delete_channel(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    channel = await channel_registry.find_one({"channel_id": channel_id, "owner_id": user_id})
    if not channel:
        await callback.answer("Channel not found!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, Delete", callback_data=f"confirm_deletechannel_{channel_id}")
    builder.button(text="❌ Cancel", callback_data=f"viewchannel_{channel_id}")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"⚠️ Delete {channel['channel_name']}?\n\n"
        f"This will remove the channel and ALL its links!\n\n"
        f"This action cannot be undone!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_confirm_delete_channel(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Delete from registry
    await channel_registry.delete_one({"channel_id": channel_id, "owner_id": user_id})
    
    # Delete all links
    await channels_collection.delete_many({"channel_id": channel_id, "owner_id": user_id})
    
    await callback.message.edit_text("✅ Channel deleted successfully!")
    await callback.answer("Deleted!")
    
    # Go back to channel list after 2 seconds
    import asyncio
    await asyncio.sleep(1)
    await handle_back(callback)
