package com.rustpvp.client;

import com.rustpvp.RustPvpMod;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = RustPvpMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public class ClientModEvents {

    @net.minecraftforge.eventbus.api.SubscribeEvent
    public static void onRegisterOverlays(RegisterGuiOverlaysEvent event) {
        event.registerAboveAll("rust_hud", new RustHudOverlay());
    }
}
