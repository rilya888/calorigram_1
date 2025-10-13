"""
Пакет обработчиков для Telegram бота
Централизованный импорт всех обработчиков
"""

def get_handlers():
    """Получить все обработчики с ленивой загрузкой"""
    # Импортируем обработчики регистрации
    from handlers.registration import (
        register_command,
        handle_register_callback,
        handle_gender_callback,
        handle_activity_callback,
        handle_goal_callback,
        handle_text_input_registration,
        send_not_registered_message,
        check_user_registration,
    )

    # Импортируем обработчики профиля
    from handlers.profile import (
        profile_command,
        reset_command,
        handle_statistics_callback,
        handle_stats_today_callback,
        handle_stats_yesterday_callback,
        handle_stats_week_callback,
        show_meal_statistics,
        handle_reset_confirm,
        handle_profile_callback,
    )

    # Импортируем обработчики подписки
    from handlers.subscription import (
        subscription_command,
        handle_subscription_purchase,
        handle_activate_trial_callback,
        handle_pre_checkout_query,
        handle_successful_payment,
        show_subscription_purchase_menu,
        check_subscription_access,
        get_subscription_message,
    )

    # Импортируем обработчики админки
    from handlers.admin import (
        admin_command,
        show_admin_panel,
        handle_admin_stats_callback,
        handle_admin_users_callback,
        handle_admin_meals_callback,
        handle_admin_broadcast_callback,
        handle_admin_subscriptions_callback,
        handle_admin_back_callback,
        send_broadcast_message,
        is_admin,
    )

    # Импортируем обработчики меню
    from handlers.menu import (
        start_command,
        help_command,
        terms_command,
        show_main_menu,
        show_welcome_message_with_data,
        get_main_menu_keyboard,
        get_main_menu_keyboard_for_user,
        get_analysis_result_keyboard,
        handle_back_to_main,
        handle_main_menu_callback,
        handle_menu_from_meal_selection,
        handle_help_callback,
        handle_terms_callback,
    )

    return {
        'registration': {
            'register_command': register_command,
            'handle_register_callback': handle_register_callback,
            'handle_gender_callback': handle_gender_callback,
            'handle_activity_callback': handle_activity_callback,
            'handle_goal_callback': handle_goal_callback,
            'handle_text_input_registration': handle_text_input_registration,
            'send_not_registered_message': send_not_registered_message,
            'check_user_registration': check_user_registration,
        },
        'profile': {
            'profile_command': profile_command,
            'reset_command': reset_command,
            'handle_statistics_callback': handle_statistics_callback,
            'handle_stats_today_callback': handle_stats_today_callback,
            'handle_stats_yesterday_callback': handle_stats_yesterday_callback,
            'handle_stats_week_callback': handle_stats_week_callback,
            'show_meal_statistics': show_meal_statistics,
            'handle_reset_confirm': handle_reset_confirm,
            'handle_profile_callback': handle_profile_callback,
        },
        'subscription': {
            'subscription_command': subscription_command,
            'handle_subscription_purchase': handle_subscription_purchase,
            'handle_activate_trial_callback': handle_activate_trial_callback,
            'handle_pre_checkout_query': handle_pre_checkout_query,
            'handle_successful_payment': handle_successful_payment,
            'show_subscription_purchase_menu': show_subscription_purchase_menu,
            'check_subscription_access': check_subscription_access,
            'get_subscription_message': get_subscription_message,
        },
        'admin': {
            'admin_command': admin_command,
            'show_admin_panel': show_admin_panel,
            'handle_admin_stats_callback': handle_admin_stats_callback,
            'handle_admin_users_callback': handle_admin_users_callback,
            'handle_admin_meals_callback': handle_admin_meals_callback,
            'handle_admin_broadcast_callback': handle_admin_broadcast_callback,
            'handle_admin_subscriptions_callback': handle_admin_subscriptions_callback,
            'handle_admin_back_callback': handle_admin_back_callback,
            'send_broadcast_message': send_broadcast_message,
            'is_admin': is_admin,
        },
        'menu': {
            'start_command': start_command,
            'help_command': help_command,
            'terms_command': terms_command,
            'show_main_menu': show_main_menu,
            'show_welcome_message_with_data': show_welcome_message_with_data,
            'get_main_menu_keyboard': get_main_menu_keyboard,
            'get_main_menu_keyboard_for_user': get_main_menu_keyboard_for_user,
            'get_analysis_result_keyboard': get_analysis_result_keyboard,
            'handle_back_to_main': handle_back_to_main,
            'handle_main_menu_callback': handle_main_menu_callback,
            'handle_menu_from_meal_selection': handle_menu_from_meal_selection,
            'handle_help_callback': handle_help_callback,
            'handle_terms_callback': handle_terms_callback,
        }
    }

__all__ = ['get_handlers']

