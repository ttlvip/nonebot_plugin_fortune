from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra
from typing import List, Dict, Union
from pathlib import Path
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .download import ResourceError, download_resource

'''
    抽签主题对应表，第一键值为“抽签设置”或“主题列表”展示的主题名称
    Key-Value: 主题资源文件夹名-设置主题别名
'''
FortuneThemesDict: Dict[str, List[str]] = {
    "random": ["随机"],
    "pcr": ["PCR", "公主链接", "公主连结", "Pcr", "pcr"],
    "genshin": ["原神", "Genshin Impact", "genshin", "Genshin", "op", "原批"],
    "hololive": ["Hololive", "hololive", "Vtb", "vtb", "管人", "Holo", "holo", "猴楼"],
    "touhou": ["东方", "touhou", "Touhou", "车万"],
    "touhou_lostword": ["东方归言录", "东方lostword", "touhou lostword", "Touhou dlc"],
    "touhou_old": ["旧东方", "旧版东方", "老东方", "老版东方", "经典东方"],
    "onmyoji": ["阴阳师", "yys", "Yys", "痒痒鼠"],
    "azure": ["碧蓝航线", "碧蓝", "azure", "Azure"],
    "asoul": ["Asoul", "asoul", "a手", "A手", "as", "As"],
    "arknights": ["明日方舟", "方舟", "arknights", "鹰角", "Arknights", "舟游"],
    "granblue_fantasy": ["碧蓝幻想", "Granblue Fantasy", "granblue fantasy", "幻想", "fantasy", "Fantasy"],
    "punishing":["战双", "战双帕弥什"],
    "pretty_derby": ["赛马娘", "马", "马娘", "赛马"],
    "dc4": ["dc4", "DC4", "Dc4", "初音岛", "初音岛4"],
    "einstein": ["爱因斯坦携爱敬上", "爱因斯坦", "einstein", "Einstein"],
    "sweet_illusion": ["灵感满溢的甜蜜创想", "甜蜜一家人", "富婆妹"],
    "liqingge": ["李清歌", "清歌"],
    "hoshizora": ["星空列车与白的旅行", "星空列车"],
    "sakura": ["樱色之云绯色之恋", "樱云之恋", "樱云绯恋", "樱云"],
    "summer_pockets": ["夏日口袋", "夏兜", "sp", "SP"],
    "amazing_grace": ["奇异恩典"],
    "ark_order": ["方舟指令"]
}

class PluginConfig(BaseModel, extra=Extra.ignore):
    fortune_path: Path = Path(__file__).parent / "resource"

class ThemesFlagConfig(BaseModel, extra=Extra.ignore):
    '''
        Switches of themes only valid in random divination.
        Make sure NOT ALL FALSE!
    '''
    amazing_grace_flag: bool = True
    arknights_flag: bool = True
    asoul_flag: bool = True
    azure_flag: bool = True
    genshin_flag:  bool = True
    onmyoji_flag: bool = True
    pcr_flag: bool = True
    touhou_flag: bool = True
    touhou_lostword_flag: bool = True
    touhou_old_flag: bool = True
    hololive_flag: bool = True
    granblue_fantasy_flag: bool = True
    punishing_flag: bool = True
    pretty_derby_flag: bool = True
    dc4_flag: bool = True
    einstein_flag: bool = True
    sweet_illusion_flag: bool = True
    liqingge_flag: bool = True
    hoshizora_flag: bool = True
    sakura_flag: bool = True 
    summer_pockets_flag: bool = True
    ark_order_flag: bool = True

driver = get_driver()
fortune_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())
themes_flag_config: ThemesFlagConfig = ThemesFlagConfig.parse_obj(driver.config.dict())

@driver.on_startup
async def fortune_check() -> None:
    if not fortune_config.fortune_path.exists():
        fortune_config.fortune_path.mkdir(parents=True, exist_ok=True)
    
    '''
        Check whether all themes are disable.
    '''
    content = themes_flag_config.dict()
    _flag: bool = False
    for theme in content:
        if content.get(theme, False):
            _flag = True
            break
    
    if not _flag:
        raise ResourceError("Fortune themes ALL disabled! Please check!")
    
    # Save fortune themes config
    flags_config_path: Path = fortune_config.fortune_path / "fortune_config.json"            
    with flags_config_path.open("w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    
    '''
        Check fonts.
        TODO download fonts from raw.fastgit.org is ALWAYS FAILED!
        In version v0.4.x, disable downloading. 
    '''
    fonts_path: Path = fortune_config.fortune_path / "font"
    if not fonts_path.exists():
        fonts_path.mkdir(parents=True, exist_ok=True)
    
    if not (fonts_path / "Mamelon.otf").exists():
        # ret = await download_resource((fonts_path / "Mamelon.otf"), "Mamelon.otf", "font")
        # if ret:
        #     logger.info(f"Downloaded Mamelon.otf from repo")
        # else:
        raise ResourceError(f"Resource Mamelon.otf is missing! Please check!")
    
    if not (fonts_path / "sakura.ttf").exists():
        # ret = await download_resource((fonts_path / "sakura.ttf"), "sakura.ttf", "font")
        # if ret:
        #     logger.info(f"Downloaded sakura.ttf from repo")
        # else:
        raise ResourceError(f"Resource sakura.ttf is missing! Please check!")
    
    '''
        Try to get the latest copywriting from the repository.
    '''
    copywriting_path: Path = fortune_config.fortune_path / "fortune" / "copywriting.json"
    if not copywriting_path.parent.exists():
        copywriting_path.parent.mkdir(parents=True, exist_ok=True)
    
    ret = await download_resource(copywriting_path, "copywriting.json", "fortune")
    if not ret and not copywriting_path.exists():
        raise ResourceError(f"Resource copywriting.json is missing! Please check!")
    
    '''
        Check rules and data json files
    '''
    fortune_data_path: Path = fortune_config.fortune_path / "fortune_data.json"
    fortune_setting_path: Path = fortune_config.fortune_path / "fortune_setting.json"
    group_rules_path: Path = fortune_config.fortune_path / "group_rules.json"
    specific_rules_path: Path = fortune_config.fortune_path / "specific_rules.json"
    
    if not fortune_data_path.exists():
        logger.warning("Resource fortune_data.json is missing, initialized one...")
        
        with fortune_data_path.open("w", encoding="utf-8") as f:
            json.dump(dict(), f, ensure_ascii=False, indent=4)
    
    _flag = False
    if not group_rules_path.exists():        
        # In version 0.4.x, compatible job will be done automatically if group_rules.json doesn't exist
        if fortune_setting_path.exists():
            # Try to transfer from the old setting json
            ret = group_rules_transfer(fortune_setting_path, group_rules_path)
            if ret:
                logger.info("旧版 fortune_setting.json 文件中群聊抽签主题设置已更新至 group_rules.json")
                _flag = True
        
        if not _flag:
            # If failed or fortune_setting_path doesn't exist, initialize group_rules.json instead
            with group_rules_path.open("w", encoding="utf-8") as f:
                json.dump(dict(), f, ensure_ascii=False, indent=4)
            
            logger.info("旧版 fortune_setting.json 文件中群聊抽签主题设置不存在，初始化 group_rules.json")

    _flag = False
    if not specific_rules_path.exists():
        # In version 0.4.9 and 0.4.10, data transfering will be done automatically if specific_rules.json doesn't exist
        if fortune_setting_path.exists():
            # Try to transfer from the old setting json
            ret = specific_rules_transfer(fortune_setting_path, specific_rules_path)
            if ret:
                logger.info("旧版 fortune_setting.json 文件中签底指定规则已更新至 specific_rules.json")
                logger.warning("指定签底抽签功能将在 v0.5.x 弃用")
                _flag = True
        
        if not _flag:
            # Try to download it from repo
            ret = await download_resource(specific_rules_path, "specific_rules.json")
            if ret:
                logger.info(f"Downloaded specific_rules.json from repo")
            else:
                # If failed, initialize specific_rules.json instead
                with specific_rules_path.open("w", encoding="utf-8") as f:
                    json.dump(dict(), f, ensure_ascii=False, indent=4)
                
                logger.info("旧版 fortune_setting.json 文件中签底指定规则不存在，初始化 specific_rules.json")
                logger.warning("指定签底抽签功能将在 v0.5.x 弃用")

def group_rules_transfer(fortune_setting_dir: Path, group_rules_dir: Path) -> bool:
    '''
        Transfer the group_rule in fortune_setting.json to group_rules.json
    '''
    with open(fortune_setting_dir, 'r', encoding='utf-8') as fs:
        _setting: Dict[str, Dict[str, Union[str, List[str]]]] = json.load(fs)
        group_rules = _setting.get("group_rule", None)  # Old key is group_rule
    
        with open(group_rules_dir, 'w', encoding='utf-8') as fr:
            if not group_rules:
                json.dump(dict(), fr, ensure_ascii=False, indent=4)
                return False
            else:
                json.dump(group_rules, fr, ensure_ascii=False, indent=4)
                return True

def specific_rules_transfer(fortune_setting_dir: Path, specific_rules_dir: Path) -> bool:
    '''
        Transfer the specific_rule in fortune_setting.json to specific_rules.json
    '''
    with open(fortune_setting_dir, 'r', encoding='utf-8') as fs:
        _setting: Dict[str, Dict[str, Union[str, List[str]]]] = json.load(fs)
        specific_rules = _setting.get("specific_rule", None)  # Old key is specific_rule
        
        with open(specific_rules_dir, 'w', encoding='utf-8') as fr:
            if not specific_rules:
                json.dump(dict(), fr, ensure_ascii=False, indent=4)
                return False
            else:
                json.dump(specific_rules, fr, ensure_ascii=False, indent=4)
                return True