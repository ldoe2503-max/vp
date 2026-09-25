package com.rustpvp.item;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.server.level.ServerLevel;

import java.util.Optional;

/**
 * Хитскан-оружие: мгновенный луч от глаз игрока, а не физическая пуля-сущность.
 * Это стандартный, надёжный подход для оружейных модов -- избегает сложностей
 * с сетевой синхронизацией снарядов между клиентом и сервером.
 */
public class AKItem extends Item {

    private static final double RANGE = 60.0;
    private static final float DAMAGE = 6.0F;
    private static final int COOLDOWN_TICKS = 6; // ~3 выстрела в секунду

    public AKItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack heldStack = player.getItemInHand(hand);

        if (player.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.fail(heldStack);
        }

        ItemStack ammoStack = findAmmo(player);
        if (ammoStack.isEmpty() && !player.getAbilities().instabuild) {
            player.displayClientMessage(
                    net.minecraft.network.chat.Component.literal("Нет патронов"), true);
            return InteractionResultHolder.fail(heldStack);
        }

        player.getCooldowns().addCooldown(this, COOLDOWN_TICKS);

        if (!level.isClientSide) {
            if (!player.getAbilities().instabuild) {
                ammoStack.shrink(1);
            }
            fireShot((ServerLevel) level, player);
        }

        player.swing(hand, true);
        return InteractionResultHolder.consume(heldStack);
    }

    private ItemStack findAmmo(Player player) {
        for (ItemStack stack : player.getInventory().items) {
            if (stack.is(ModItems.AK_AMMO.get())) {
                return stack;
            }
        }
        return ItemStack.EMPTY;
    }

    private void fireShot(ServerLevel level, Player player) {
        Vec3 start = player.getEyePosition(1.0F);
        Vec3 look = player.getLookAngle();
        Vec3 end = start.add(look.scale(RANGE));

        BlockHitResult blockHit = level.clip(new ClipContext(
                start, end,
                ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,
                player
        ));
        double blockDistance = blockHit.getType() == HitResult.Type.MISS
                ? RANGE
                : start.distanceTo(blockHit.getLocation());

        LivingEntity closestHit = null;
        double closestDistance = blockDistance;

        for (net.minecraft.world.entity.Entity entity :
                level.getEntities(player, player.getBoundingBox().expandTowards(look.scale(RANGE)).inflate(1.0D))) {
            if (!(entity instanceof LivingEntity) || !entity.isPickable()) {
                continue;
            }
            LivingEntity living = (LivingEntity) entity;

            Optional<Vec3> hitPos = living.getBoundingBox().inflate(0.3D).clip(start, end);
            if (hitPos.isEmpty()) {
                continue;
            }
            double distance = start.distanceTo(hitPos.get());
            if (distance < closestDistance) {
                closestDistance = distance;
                closestHit = living;
            }
        }

        Vec3 impactPoint = start.add(look.scale(closestDistance));
        level.sendParticles(ParticleTypes.SMOKE, impactPoint.x, impactPoint.y, impactPoint.z, 4, 0.05, 0.05, 0.05, 0.01);
        level.playSound(null, player.blockPosition(), SoundEvents.CROSSBOW_SHOOT, SoundSource.PLAYERS, 1.2F, 0.9F);

        if (closestHit != null) {
            closestHit.hurt(player.damageSources().playerAttack(player), DAMAGE);
            level.sendParticles(ParticleTypes.CRIT, impactPoint.x, impactPoint.y, impactPoint.z, 6, 0.1, 0.1, 0.1, 0.05);
        }
    }
}
