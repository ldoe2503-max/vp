package com.rustpvp;

import com.rustpvp.item.ModItems;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public class ModCreativeTabs {

    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(ForgeRegistries.CREATIVE_MODE_TABS, RustPvpMod.MODID);

    public static final RegistryObject<CreativeModeTab> RUSTPVP_TAB = TABS.register("rustpvp_tab",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.rustpvp"))
                    .icon(() -> new ItemStack(ModItems.AK47.get()))
                    .displayItems((parameters, output) -> {
                        output.accept(ModItems.AK47.get());
                        output.accept(ModItems.AK_AMMO.get());
                        output.accept(ModItems.BANDAGE.get());
                    })
                    .build());
}
