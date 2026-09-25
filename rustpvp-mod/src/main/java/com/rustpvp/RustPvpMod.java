package com.rustpvp;

import com.rustpvp.item.ModItems;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod(RustPvpMod.MODID)
public class RustPvpMod {

    public static final String MODID = "rustpvp";
    public static final Logger LOGGER = LoggerFactory.getLogger(MODID);

    public RustPvpMod(FMLJavaModLoadingContext context) {
        IEventBus modEventBus = context.getModEventBus();

        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.TABS.register(modEventBus);

        LOGGER.info("RustPvP mod loaded: AK-47, ammo, bandage, HUD.");
    }
}
