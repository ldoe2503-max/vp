package com.rustpvp.item;

import com.rustpvp.RustPvpMod;
import net.minecraft.world.item.Item;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public class ModItems {

    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, RustPvpMod.MODID);

    public static final RegistryObject<Item> AK_AMMO = ITEMS.register("ak_ammo",
            () -> new Item(new Item.Properties().stacksTo(60)));

    public static final RegistryObject<Item> AK47 = ITEMS.register("ak47",
            () -> new AKItem(new Item.Properties().stacksTo(1)));

    public static final RegistryObject<Item> BANDAGE = ITEMS.register("bandage",
            () -> new BandageItem(new Item.Properties().stacksTo(16)));
}
