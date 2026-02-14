import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import ChatMemberUpdatedFilter
from gateway.config import BOT_TOKEN
from gateway.handlers import start, join, addchannel, autoadd, callbacks, join_request, broadcast, stats

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.message.register(start.start, start.StartFilter())
    dp.message.register(join.join, join.JoinFilter())
    dp.message.register(addchannel.addchannel, addchannel.AddChannelFilter())
    dp.message.register(addchannel.mychannels, addchannel.MyChannelsFilter())
    dp.message.register(broadcast.broadcast, broadcast.BroadcastFilter())
    dp.message.register(stats.stats, stats.StatsFilter())
    dp.message.register(autoadd.handle_forward, F.forward_from_chat)
    dp.my_chat_member.register(autoadd.bot_added_as_admin, ChatMemberUpdatedFilter(member_status_changed=True))
    
    dp.callback_query.register(callbacks.handle_stats, F.data.startswith("stats_"))
    dp.callback_query.register(callbacks.handle_delete, F.data.startswith("delete_"))
    dp.callback_query.register(callbacks.handle_confirm_delete, F.data.startswith("confirm_delete_"))
    dp.callback_query.register(callbacks.handle_toggle_auto, F.data.startswith("toggle_auto_"))
    dp.callback_query.register(callbacks.handle_manage_links, F.data.startswith("managelinks_"))
    dp.callback_query.register(callbacks.handle_revoke_link, F.data.startswith("revoke_"))
    dp.callback_query.register(callbacks.handle_new_link, F.data.startswith("newlink_"))
    dp.callback_query.register(callbacks.handle_view_channel, F.data.startswith("viewchannel_"))
    dp.callback_query.register(callbacks.handle_toggle_auto_channel, F.data.startswith("toggle_auto_channel_"))
    dp.callback_query.register(callbacks.handle_delete_channel, F.data.startswith("deletechannel_"))
    dp.callback_query.register(callbacks.handle_confirm_delete_channel, F.data.startswith("confirm_deletechannel_"))
    dp.callback_query.register(callbacks.handle_help, F.data == "help")
    dp.callback_query.register(callbacks.handle_my_channels_btn, F.data == "my_channels_btn")
    dp.callback_query.register(callbacks.handle_back, F.data == "back_to_channels")
    dp.callback_query.register(callbacks.handle_back_to_start, F.data == "back_to_start")
    
    dp.chat_join_request.register(join_request.handle_join_request)
    
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
