'''IRC Numeric Message Constants'''
IRC_MODES = ['a', 's', 'i', 'w', 'o', 'O', 'r' ]
IRC_USER_MODES = [ 'i', 'w', 'o', 'O', 'r' ]
IRC_CHANNEL_MODES = ['o', 'p', 's', 'i', 't', 'n', 'b', 'v']

RPL_WELCOME = 1
RPL_YOURHOST = 2
RPL_CREATED = 3
RPL_MYINFO = 4
RPL_BOUNCE = 5
RPL_TRACELINK = 200
RPL_TRACECONNECTING = 201
RPL_TRACEHANDSHAKE = 202
RPL_TRACEUNKNOWN = 203
RPL_TRACEOPERATOR = 204
RPL_TRACEUSER = 205
RPL_TRACESERVER = 206
RPL_TRACESERVICE = 207
RPL_TRACENEWTYPE = 208
RPL_TRACECLASS = 209
RPL_TRACERECONNECT = 210
RPL_STATSLINKINFO = 211
RPL_STATSCOMMANDS = 212
RPL_STATSCLINE = 213
RPL_STATSNLINE = 214
RPL_STATSILINE = 215
RPL_STATSKLINE = 216
RPL_STATSQLINE = 217
RPL_STATSYLINE = 218
RPL_ENDOFSTATS = 219
RPL_UMODEIS = 221
RPL_SERVICEINFO = 231
RPL_ENDOFSERVICES = 232
RPL_SERVICE = 233
RPL_SERVLIST = 234
RPL_SERVLISTEND = 235
RPL_STATSVLINE = 240
RPL_STATSLLINE = 241
RPL_STATSUPTIME = 242
RPL_STATSOLINE = 243
RPL_STATSHLINE = 244
RPL_STATSPING = 246
RPL_STATSDLINE = 250
RPL_LUSERCLIENT = 251
RPL_LUSEROP = 252
RPL_LUSERUNKNOWN = 253
RPL_LUSERCHANNELS = 254
RPL_LUSERME = 255
RPL_ADMINME = 256
RPL_ADMINLOC1 = 257
RPL_ADMINLOC2 = 258
RPL_ADMINEMAIL = 259
RPL_TRACELOG = 261
RPL_TRACEEND = 262
RPL_TRYAGAIN = 263
RPL_NONE = 300
RPL_AWAY = 301
RPL_USERHOST = 302
RPL_ISON = 303
RPL_UNAWAY = 305
RPL_NOWAWAY = 306
RPL_WHOISUSER = 311
RPL_WHOISSERVER = 312
RPL_WHOISOPERATOR = 313
RPL_WHOWASUSER = 314
RPL_ENDOFWHO = 315
RPL_WHOISCHANOP = 316
RPL_WHOISIDLE = 317
RPL_ENDOFWHOIS = 318
RPL_WHOISCHANNELS = 319
RPL_LISTSTART = 321
RPL_LIST = 322
RPL_LISTEND = 323
RPL_CHANNELMODEIS = 324
RPL_UNIQOPIS = 325
RPL_NOTOPIC = 331
RPL_TOPIC = 332
RPL_INVITING = 341
RPL_SUMMONING = 342
RPL_INVITELIST = 346
RPL_ENDOFINVITELIST = 347
RPL_EXCEPTLIST = 348
RPL_ENDOFEXCEPTLIST = 349
RPL_VERSION = 351
RPL_WHOREPLY = 352
RPL_NAMREPLY = 353
RPL_KILLDONE = 361
RPL_CLOSING = 362
RPL_CLOSEEND = 363
RPL_LINKS = 364
RPL_ENDOFLINKS = 365
RPL_ENDOFNAMES = 366
RPL_BANLIST = 367
RPL_ENDOFBANLIST = 368
RPL_ENDOFWHOWAS = 369
RPL_INFO = 371
RPL_MOTD = 372
RPL_INFOSTART = 373
RPL_ENDOFINFO = 374
RPL_MOTDSTART = 375
RPL_ENDOFMOTD = 376
RPL_YOUREOPER = 381
RPL_REHASHING = 382
RPL_YOURESERVICE = 383
RPL_MYPORTIS = 384
RPL_TIME = 391
RPL_USERSSTART = 392
RPL_USERS = 393
RPL_ENDOFUSERS = 394
RPL_NOUSERS = 395
ERR_NOSUCHNICK = 401
ERR_NOSUCHSERVER = 402
ERR_NOSUCHCHANNEL = 403
ERR_CANNOTSENDTOCHAN = 404
ERR_TOOMANYCHANNELS = 405
ERR_WASNOSUCHNICK = 406
ERR_TOOMANYTARGETS = 407
ERR_NOSUCHSERVICE = 408
ERR_NOORIGIN = 409
ERR_NORECIPIENT = 411
ERR_NOTEXTTOSEND = 412
ERR_NOTOPLEVEL = 413
ERR_WILDTOPLEVEL = 414
ERR_BADMASK = 415
ERR_UNKNOWNCOMMAND = 421
ERR_NOMOTD = 422
ERR_NOADMININFO = 423
ERR_FILEERROR = 424
ERR_NONICKNAMEGIVEN = 431
ERR_ERRONEUSNICKNAME = 432
ERR_NICKNAMEINUSE = 433
ERR_NICKCOLLISION = 436
ERR_UNAVAILRESOURCE = 437
ERR_USERNOTINCHANNEL = 441
ERR_NOTONCHANNEL = 442
ERR_USERONCHANNEL = 443
ERR_NOLOGIN = 444
ERR_SUMMONDISABLED = 445
ERR_USERSDISABLED = 446
ERR_NOTREGISTERED = 451
ERR_NEEDMOREPARAMS = 461
ERR_ALREADYREGISTRED = 462
ERR_NOPERMFORHOST = 463
ERR_PASSWDMISMATCH = 464
ERR_YOUREBANNEDCREEP = 465
ERR_YOUWILLBEBANNED = 466
ERR_KEYSET = 467
ERR_CHANNELISFULL = 471
ERR_UNKNOWNMODE = 472
ERR_INVITEONLYCHAN = 473
ERR_BANNEDFROMCHAN = 474
ERR_BADCHANNELKEY = 475
ERR_BADCHANMASK = 476
ERR_NOCHANMODES = 477
ERR_BANLISTFULL = 478
ERR_NOPRIVILEGES = 481
ERR_CHANOPRIVSNEEDED = 482
ERR_CANTKILLSERVER = 483
ERR_RESTRICTED = 484
ERR_UNIQOPPRIVSNEEDED = 485
ERR_NOOPERHOST = 491
ERR_NOSERVICEHOST = 492
ERR_UMODEUNKNOWNFLAG = 501
ERR_USERSDONTMATCH = 502

IRC_CODE = {
    RPL_WELCOME :
       ("RPL_WELCOME",
        'Welcome to the Internet Relay Network %(nick)s!%(user)s@%(host)s'),
    RPL_YOURHOST :
       ("RPL_YOURHOST",
        'Your host is %(server)s, running version %(version)s'),
    RPL_CREATED :
       ("RPL_CREATED",
        'This server was created %(launched)s'),
    RPL_MYINFO :
       ("RPL_MYINFO",
        '%(server)s %(version)s %(user_modes)s %(channel_modes)s'),
    RPL_BOUNCE :
       ("RPL_BOUNCE", ""),
    RPL_TRACELINK :
       ("RPL_TRACELINK", ""),
    RPL_TRACECONNECTING :
       ("RPL_TRACECONNECTING", ""),
    RPL_TRACEHANDSHAKE :
       ("RPL_TRACEHANDSHAKE", ""),
    RPL_TRACEUNKNOWN :
       ("RPL_TRACEUNKNOWN", ""),
    RPL_TRACEOPERATOR :
       ("RPL_TRACEOPERATOR", ""),
    RPL_TRACEUSER :
       ("RPL_TRACEUSER", ""),
    RPL_TRACESERVER :
       ("RPL_TRACESERVER", ""),
    RPL_TRACESERVICE :
       ("RPL_TRACESERVICE", ""),
    RPL_TRACENEWTYPE :
       ("RPL_TRACENEWTYPE", ""),
    RPL_TRACECLASS :
       ("RPL_TRACECLASS", ""),
    RPL_TRACERECONNECT :
       ("RPL_TRACERECONNECT", ""),
    RPL_STATSLINKINFO :
       ("RPL_STATSLINKINFO", ""),
    RPL_STATSCOMMANDS :
       ("RPL_STATSCOMMANDS", ""),
    RPL_STATSCLINE :
       ("RPL_STATSCLINE", ""),
    RPL_STATSNLINE :
       ("RPL_STATSNLINE", ""),
    RPL_STATSILINE :
       ("RPL_STATSILINE", ""),
    RPL_STATSKLINE :
       ("RPL_STATSKLINE", ""),
    RPL_STATSQLINE :
       ("RPL_STATSQLINE", ""),
    RPL_STATSYLINE :
       ("RPL_STATSYLINE", ""),
    RPL_ENDOFSTATS :
       ("RPL_ENDOFSTATS", ""),
    RPL_UMODEIS :
       ("RPL_UMODEIS", "%(mode)s"),
    RPL_SERVICEINFO :
       ("RPL_SERVICEINFO", ""),
    RPL_ENDOFSERVICES :
       ("RPL_ENDOFSERVICES", ""),
    RPL_SERVICE :
       ("RPL_SERVICE", ""),
    RPL_SERVLIST :
       ("RPL_SERVLIST", ""),
    RPL_SERVLISTEND :
       ("RPL_SERVLISTEND", ""),
    RPL_STATSVLINE :
       ("RPL_STATSVLINE", ""),
    RPL_STATSLLINE :
       ("RPL_STATSLLINE", ""),
    RPL_STATSUPTIME :
       ("RPL_STATSUPTIME", ""),
    RPL_STATSOLINE :
       ("RPL_STATSOLINE", ""),
    RPL_STATSHLINE :
       ("RPL_STATSHLINE", ""),
    RPL_STATSPING :
       ("RPL_STATSPING", ""),
    RPL_STATSDLINE :
       ("RPL_STATSDLINE", ""),
    RPL_LUSERCLIENT :
       ("RPL_LUSERCLIENT",
        ':There are %(users)d users and %(services)d services on %(servers)d servers'),
    RPL_LUSEROP :
       ("RPL_LUSEROP", 
        '%(opers)d :operator(s) online'),
    RPL_LUSERUNKNOWN :
       ("RPL_LUSERUNKNOWN",
        '%(unknown)d :unknown connection(s)'),
    RPL_LUSERCHANNELS :
       ("RPL_LUSERCHANNELS", 
        '%(channels)d :channels formed'),
    RPL_LUSERME :
       ("RPL_LUSERME",
        ':I have %(clients)d clients and %(servers)d servers'),
    RPL_ADMINME :
       ("RPL_ADMINME", ""),
    RPL_ADMINLOC1 :
       ("RPL_ADMINLOC1", ""),
    RPL_ADMINLOC2 :
       ("RPL_ADMINLOC2", ""),
    RPL_ADMINEMAIL :
       ("RPL_ADMINEMAIL", ""),
    RPL_TRACELOG :
       ("RPL_TRACELOG", ""),
    RPL_TRACEEND :
       ("RPL_TRACEEND", ""),
    RPL_TRYAGAIN :
       ("RPL_TRYAGAIN", ""),
    RPL_NONE :
       ("RPL_NONE", ""),
    RPL_AWAY :
       ("RPL_AWAY", ""),
    RPL_USERHOST :
       ("RPL_USERHOST", ""),
    RPL_ISON :
       ("RPL_ISON", ""),
    RPL_UNAWAY :
       ("RPL_UNAWAY",
        ":You are no longer marked as being away"),
    RPL_NOWAWAY :
       ("RPL_NOWAWAY", ""),
    RPL_WHOISUSER :
       ("RPL_WHOISUSER", ""),
    RPL_WHOISSERVER :
       ("RPL_WHOISSERVER", ""),
    RPL_WHOISOPERATOR :
       ("RPL_WHOISOPERATOR", ""),
    RPL_WHOWASUSER :
       ("RPL_WHOWASUSER", ""),
    RPL_ENDOFWHO :
       ("RPL_ENDOFWHO", ":End of WHO list"),
    RPL_WHOISCHANOP :
       ("RPL_WHOISCHANOP", ""),
    RPL_WHOISIDLE :
       ("RPL_WHOISIDLE", ""),
    RPL_ENDOFWHOIS :
       ("RPL_ENDOFWHOIS", ""),
    RPL_WHOISCHANNELS :
       ("RPL_WHOISCHANNELS", ""),
    RPL_LISTSTART :
       ("RPL_LISTSTART", ""),
    RPL_LIST :
       ("RPL_LIST", "%(channel)s %(visible)d :%(topic)s"),
    RPL_LISTEND :
       ("RPL_LISTEND", ":End of LIST"),
    RPL_CHANNELMODEIS :
       ("RPL_CHANNELMODEIS", "%(channel)s %(modes)s %(params)s"),
    RPL_UNIQOPIS :
       ("RPL_UNIQOPIS", "%(channel)s %(nickname)s"),
    RPL_NOTOPIC :
       ("RPL_NOTOPIC",
        "%(channel)s :No topic is set"),
    RPL_TOPIC :
       ("RPL_TOPIC", "%(channel)s :%(topic)s"),
    RPL_INVITING :
       ("RPL_INVITING", '%(nickname)s %(channel)s'),
    RPL_SUMMONING :
       ("RPL_SUMMONING", ""),
    RPL_INVITELIST :
       ("RPL_INVITELIST", "%(channel)s %(mask)s"),
    RPL_ENDOFINVITELIST :
       ("RPL_ENDOFINVITELIST", 
        "%s :End of channel invite list"),
    RPL_EXCEPTLIST :
       ("RPL_EXCEPTLIST", "%(channel)s %(mask)s"),
    RPL_ENDOFEXCEPTLIST :
       ("RPL_ENDOFEXCEPTLIST",
        "%(channel)s :End of channel exception list"),
    RPL_VERSION :
       ("RPL_VERSION",
        '%(version)s.%(debug)d %(server)s :%(comment)s'),
    RPL_WHOREPLY :
       ("RPL_WHOREPLY",
        "%(channel)s %(user)s %(host)s %(server)s %(nick)s "\
            "%(foo1)s %(foo2)s :%(hopcount)d %(realname)s"),
    RPL_NAMREPLY :
       ("RPL_NAMREPLY", '= %(channel)s :%(nick)s'),
    RPL_KILLDONE :
       ("RPL_KILLDONE", ""),
    RPL_CLOSING :
       ("RPL_CLOSING", ""),
    RPL_CLOSEEND :
       ("RPL_CLOSEEND", ""),
    RPL_LINKS :
       ("RPL_LINKS", ""),
    RPL_ENDOFLINKS :
       ("RPL_ENDOFLINKS", ""),
    RPL_ENDOFNAMES :
       ("RPL_ENDOFNAMES", '%(channel)s :End of NAMES list'),
    RPL_BANLIST :
       ("RPL_BANLIST", "%(channel)s %(mask)s"),
    RPL_ENDOFBANLIST :
       ("RPL_ENDOFBANLIST", "%(channel)s :End of channel ban list"),
    RPL_ENDOFWHOWAS :
       ("RPL_ENDOFWHOWAS", ""),
    RPL_INFO :
       ("RPL_INFO", ':%(info)s'),
    RPL_MOTD :
       ("RPL_MOTD", ":- %(motd_line)s"),
    RPL_INFOSTART :
       ("RPL_INFOSTART", ""),
    RPL_ENDOFINFO :
       ("RPL_ENDOFINFO", ':End of INFO list'),
    RPL_MOTDSTART :
       ("RPL_MOTDSTART", ":- %(server)s Message of the day - "),
    RPL_ENDOFMOTD :
       ("RPL_ENDOFMOTD", ":End of MOTD command"),
    RPL_YOUREOPER :
       ("RPL_YOUREOPER", ':You are now an IRC operator'),
    RPL_REHASHING :
       ("RPL_REHASHING", ""),
    RPL_YOURESERVICE :
       ("RPL_YOURESERVICE", ""),
    RPL_MYPORTIS :
       ("RPL_MYPORTIS", ""),
    RPL_TIME :
       ("RPL_TIME", "%(server)s :%(time)s"),
    RPL_USERSSTART :
       ("RPL_USERSSTART", ""),
    RPL_USERS :
       ("RPL_USERS", ""),
    RPL_ENDOFUSERS :
       ("RPL_ENDOFUSERS", ""),
    RPL_NOUSERS :
       ("RPL_NOUSERS", ""),
    ERR_NOSUCHNICK :
       ("ERR_NOSUCHNICK", 
        '%(nickname)s :No such nick/channel'),
    ERR_NOSUCHSERVER :
       ("ERR_NOSUCHSERVER", '%(server)s :No such server'),
    ERR_NOSUCHCHANNEL :
       ("ERR_NOSUCHCHANNEL", "%(channel)s :No such channel"),
    ERR_CANNOTSENDTOCHAN :
       ("ERR_CANNOTSENDTOCHAN", ""),
    ERR_TOOMANYCHANNELS :
       ("ERR_TOOMANYCHANNELS", ""),
    ERR_WASNOSUCHNICK :
       ("ERR_WASNOSUCHNICK", ""),
    ERR_TOOMANYTARGETS :
       ("ERR_TOOMANYTARGETS", ""),
    ERR_NOSUCHSERVICE :
       ("ERR_NOSUCHSERVICE", ""),
    ERR_NOORIGIN :
       ("ERR_NOORIGIN", ""),
    ERR_NORECIPIENT :
       ("ERR_NORECIPIENT",
        ':No recipient given (%(command)s)'),
    ERR_NOTEXTTOSEND :
       ("ERR_NOTEXTTOSEND", ':No text to send'),
    ERR_NOTOPLEVEL :
       ("ERR_NOTOPLEVEL", ""),
    ERR_WILDTOPLEVEL :
       ("ERR_WILDTOPLEVEL", ""),
    ERR_BADMASK :
       ("ERR_BADMASK", ""),
    ERR_UNKNOWNCOMMAND :
       ("ERR_UNKNOWNCOMMAND", ""),
    ERR_NOMOTD :
       ("ERR_NOMOTD", ":MOTD File is missing"),
    ERR_NOADMININFO :
       ("ERR_NOADMININFO", ""),
    ERR_FILEERROR :
       ("ERR_FILEERROR", ""),
    ERR_NONICKNAMEGIVEN :
       ("ERR_NONICKNAMEGIVEN", ':No nickname given'),
    ERR_ERRONEUSNICKNAME :
       ("ERR_ERRONEUSNICKNAME", ""),
    ERR_NICKNAMEINUSE :
       ("ERR_NICKNAMEINUSE", '%(nickname)s :Nickname is already in use'),
    ERR_NICKCOLLISION :
       ("ERR_NICKCOLLISION", ""),
    ERR_UNAVAILRESOURCE :
       ("ERR_UNAVAILRESOURCE", ""),
    ERR_USERNOTINCHANNEL :
       ("ERR_USERNOTINCHANNEL",
        "%(nickname)s %(channel)s :They aren't on that channel"),
    ERR_NOTONCHANNEL :
       ("ERR_NOTONCHANNEL",
        "%{channel_name}s :You're not on that channel"),
    ERR_USERONCHANNEL :
       ("ERR_USERONCHANNEL",
        '%(nickname)s %(channel)s :is already on channel'),
    ERR_NOLOGIN :
       ("ERR_NOLOGIN", ""),
    ERR_SUMMONDISABLED :
       ("ERR_SUMMONDISABLED", ""),
    ERR_USERSDISABLED :
       ("ERR_USERSDISABLED", ""),
    ERR_NOTREGISTERED :
       ("ERR_NOTREGISTERED", ""),
    ERR_NEEDMOREPARAMS :
       ("ERR_NEEDMOREPARAMS", 
        "%(command)s :Not enough parameters"),
    ERR_ALREADYREGISTRED :
       ("ERR_ALREADYREGISTRED",
        ':Unauthorized command (already registered)'),
    ERR_NOPERMFORHOST :
       ("ERR_NOPERMFORHOST", ""),
    ERR_PASSWDMISMATCH :
       ("ERR_PASSWDMISMATCH", ':Password incorrect'),
    ERR_YOUREBANNEDCREEP :
       ("ERR_YOUREBANNEDCREEP", ""),
    ERR_YOUWILLBEBANNED :
       ("ERR_YOUWILLBEBANNED", ""),
    ERR_KEYSET :
       ("ERR_KEYSET", "%(channel)s :Channel key already set"),
    ERR_CHANNELISFULL :
       ("ERR_CHANNELISFULL", ""),
    ERR_UNKNOWNMODE :
       ("ERR_UNKNOWNMODE",
        "%(mode)s :is unknown mode char to me for %(channel)s"),
    ERR_INVITEONLYCHAN :
       ("ERR_INVITEONLYCHAN", ""),
    ERR_BANNEDFROMCHAN :
       ("ERR_BANNEDFROMCHAN", ""),
    ERR_BADCHANNELKEY :
       ("ERR_BADCHANNELKEY", ""),
    ERR_BADCHANMASK :
       ("ERR_BADCHANMASK", ""),
    ERR_NOCHANMODES :
       ("ERR_NOCHANMODES",
        "%(channel)s :Channel doesn't support modes"),
    ERR_BANLISTFULL :
       ("ERR_BANLISTFULL", ""),
    ERR_NOPRIVILEGES :
       ("ERR_NOPRIVILEGES", ""),
    ERR_CHANOPRIVSNEEDED :
       ("ERR_CHANOPRIVSNEEDED",
        "%(channel)s :You're not channel operator"),
    ERR_CANTKILLSERVER :
       ("ERR_CANTKILLSERVER", ""),
    ERR_RESTRICTED :
       ("ERR_RESTRICTED", ""),
    ERR_UNIQOPPRIVSNEEDED :
       ("ERR_UNIQOPPRIVSNEEDED", ""),
    ERR_NOOPERHOST :
       ("ERR_NOOPERHOST", ':No O-lines for your host'),
    ERR_NOSERVICEHOST :
       ("ERR_NOSERVICEHOST", ""),
    ERR_UMODEUNKNOWNFLAG :
       ("ERR_UMODEUNKNOWNFLAG", ":Unknown MODE flag"),
    ERR_USERSDONTMATCH :
       ("ERR_USERSDONTMATCH",
        ":Cannot change mode for other users"),
}

CHANNEL_PREFIX = ['&', '#', '+', '!']

def is_channel_name(name):
    return len(name[1:]) < 200 and name[0] in CHANNEL_PREFIX

def mode_str(modes):
    '''Return a  concatenated string of active mode flags.
    Input is a dictionary of single char flag IDs to boolean.'''
    return ''.join([mode for mode, enabled in modes.items() if enabled])
